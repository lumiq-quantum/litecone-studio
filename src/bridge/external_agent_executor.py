"""External Agent Executor (HTTP-Kafka Bridge) implementation."""

import asyncio
import json
import logging
from typing import Optional, Dict, Any
import httpx

from src.kafka_client.consumer import KafkaConsumerClient
from src.kafka_client.producer import KafkaProducerClient
from src.agent_registry.client import AgentRegistryClient
from src.agent_registry.models import AgentMetadata, RetryConfig
from src.models.kafka_messages import AgentTask, AgentResult
from src.utils.logging import set_correlation_id, log_event
from src.bridge.circuit_breaker import (
    CircuitBreakerManager,
    CircuitBreakerConfig,
    CircuitBreakerOpenError
)

logger = logging.getLogger(__name__)


class ExternalAgentExecutor:
    """
    HTTP-Kafka Bridge that translates between Kafka messages and HTTP calls to external agents.
    
    This service consumes agent tasks from Kafka, invokes external agents via HTTP,
    and publishes results back to Kafka.
    """
    
    def __init__(
        self,
        kafka_bootstrap_servers: str,
        agent_registry_url: str,
        redis_url: str,
        circuit_breaker_config: CircuitBreakerConfig,
        tasks_topic: str = "orchestrator.tasks.http",
        results_topic: str = "results.topic",
        consumer_group_id: str = "external-agent-executor-group",
        http_timeout_seconds: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize the External Agent Executor.
        
        Args:
            kafka_bootstrap_servers: Comma-separated list of Kafka broker addresses
            agent_registry_url: Base URL of the Agent Registry service
            redis_url: Redis connection URL for circuit breaker
            circuit_breaker_config: Default circuit breaker configuration
            tasks_topic: Kafka topic to consume agent tasks from
            results_topic: Kafka topic to publish agent results to
            consumer_group_id: Consumer group ID for Kafka consumer
            http_timeout_seconds: Default timeout for HTTP requests to agents
            max_retries: Default maximum number of retry attempts for HTTP calls
        """
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.agent_registry_url = agent_registry_url
        self.redis_url = redis_url
        self.circuit_breaker_default_config = circuit_breaker_config
        self.tasks_topic = tasks_topic
        self.results_topic = results_topic
        self.consumer_group_id = consumer_group_id
        self.http_timeout_seconds = http_timeout_seconds
        self.max_retries = max_retries
        
        # Initialize Kafka consumer for tasks
        self.kafka_consumer: Optional[KafkaConsumerClient] = None
        
        # Initialize Kafka producer for results
        self.kafka_producer: Optional[KafkaProducerClient] = None
        
        # Initialize Agent Registry client
        self.agent_registry: Optional[AgentRegistryClient] = None
        
        # Initialize HTTP client for agent invocations
        self.http_client: Optional[httpx.AsyncClient] = None
        
        # Initialize Circuit Breaker Manager
        self.circuit_breaker_manager: Optional[CircuitBreakerManager] = None
        
        # Flag to control the main loop
        self._running = False
        
        logger.info(
            "Initialized ExternalAgentExecutor",
            extra={
                'kafka_bootstrap_servers': kafka_bootstrap_servers,
                'agent_registry_url': agent_registry_url,
                'tasks_topic': tasks_topic,
                'results_topic': results_topic,
                'consumer_group_id': consumer_group_id,
                'http_timeout_seconds': http_timeout_seconds,
                'max_retries': max_retries
            }
        )
    
    async def initialize(self) -> None:
        """
        Initialize all connections and clients.
        
        This method must be called before starting the executor.
        """
        logger.info("Initializing External Agent Executor connections...")
        
        # Initialize Kafka consumer
        self.kafka_consumer = KafkaConsumerClient(
            topics=[self.tasks_topic],
            bootstrap_servers=self.kafka_bootstrap_servers,
            group_id=self.consumer_group_id,
            client_id='external-agent-executor-consumer'
        )
        self.kafka_consumer.connect()
        logger.info(f"Kafka consumer connected to topic '{self.tasks_topic}'")
        
        # Initialize Kafka producer
        self.kafka_producer = KafkaProducerClient(
            bootstrap_servers=self.kafka_bootstrap_servers,
            client_id='external-agent-executor-producer'
        )
        self.kafka_producer.connect()
        logger.info(f"Kafka producer connected for topic '{self.results_topic}'")
        
        # Initialize Agent Registry client
        self.agent_registry = AgentRegistryClient(
            registry_url=self.agent_registry_url,
            cache_ttl_seconds=300,  # 5 minutes cache
            retry_config=RetryConfig(
                max_retries=self.max_retries,
                initial_delay_ms=1000,
                max_delay_ms=30000,
                backoff_multiplier=2.0
            )
        )
        logger.info("Agent Registry client initialized")
        
        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.http_timeout_seconds)
        )
        logger.info(f"HTTP client initialized with timeout={self.http_timeout_seconds}s")
        
        # Initialize Circuit Breaker Manager
        self.circuit_breaker_manager = CircuitBreakerManager(
            redis_url=self.redis_url,
            default_config=self.circuit_breaker_default_config
        )
        await self.circuit_breaker_manager.initialize()
        logger.info("Circuit Breaker Manager initialized")
        
        logger.info("External Agent Executor initialization complete")

    async def start(self) -> None:
        """
        Start the External Agent Executor main loop.
        
        Consumes tasks from Kafka and processes them asynchronously.
        This method runs indefinitely until stop() is called.
        """
        if not all([self.kafka_consumer, self.kafka_producer, self.agent_registry, self.http_client]):
            raise RuntimeError("Executor not initialized. Call initialize() first.")
        
        self._running = True
        logger.info("Starting External Agent Executor main loop...")
        
        try:
            # Start consuming messages with the task handler
            await self.kafka_consumer.consume(
                message_handler=self._handle_task_message,
                timeout_ms=1000
            )
        except Exception as e:
            logger.error(f"Error in main consumption loop: {e}", extra={'error': str(e)})
            raise
        finally:
            logger.info("External Agent Executor main loop stopped")
    
    async def _handle_task_message(self, message: Dict[str, Any]) -> None:
        """
        Handle a single task message from Kafka.
        
        Deserializes the message, processes the task asynchronously,
        and handles any errors that occur during processing.
        
        Args:
            message: Raw message dictionary from Kafka
        """
        try:
            # Deserialize the message into AgentTask
            task = AgentTask(**message)
            
            # Set correlation ID for all logs in this task context
            set_correlation_id(task.correlation_id)
            
            log_event(
                logger, 'info', 'task_received',
                f"Received task for agent '{task.agent_name}'",
                run_id=task.run_id,
                task_id=task.task_id,
                agent_name=task.agent_name,
                correlation_id=task.correlation_id
            )
            
            # Process the task asynchronously
            await self.process_task(task)
            
        except Exception as e:
            log_event(
                logger, 'error', 'task_error',
                f"Error handling task message: {e}",
                error=str(e),
                error_type=type(e).__name__,
                message=message
            )
            # Continue processing other messages even if one fails
    
    def stop(self) -> None:
        """
        Stop the External Agent Executor.
        
        Signals the main loop to stop consuming messages.
        """
        logger.info("Stopping External Agent Executor...")
        self._running = False
        if self.kafka_consumer:
            self.kafka_consumer.stop()
    
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the External Agent Executor.
        
        Closes all connections and cleans up resources.
        """
        logger.info("Shutting down External Agent Executor...")
        
        self.stop()
        
        # Close Kafka consumer
        if self.kafka_consumer:
            self.kafka_consumer.close()
            logger.info("Kafka consumer closed")
        
        # Close Kafka producer
        if self.kafka_producer:
            self.kafka_producer.close()
            logger.info("Kafka producer closed")
        
        # Close Agent Registry client
        if self.agent_registry:
            await self.agent_registry.close()
            logger.info("Agent Registry client closed")
        
        # Close HTTP client
        if self.http_client:
            await self.http_client.aclose()
            logger.info("HTTP client closed")
        
        # Close Circuit Breaker Manager
        if self.circuit_breaker_manager:
            await self.circuit_breaker_manager.close()
            logger.info("Circuit Breaker Manager closed")
        
        logger.info("External Agent Executor shutdown complete")

    async def process_task(self, task: AgentTask) -> None:
        """
        Process a single agent task.
        
        Queries the Agent Registry, invokes the agent with retry logic,
        handles the response, and publishes the result to Kafka.
        
        Args:
            task: The agent task to process
        """
        try:
            # Step 1: Query Agent Registry for agent metadata
            log_event(
                logger, 'info', 'agent_metadata_fetch',
                f"Fetching metadata for agent '{task.agent_name}'",
                agent_name=task.agent_name,
                task_id=task.task_id,
                run_id=task.run_id,
                correlation_id=task.correlation_id
            )
            
            agent_metadata = await self.agent_registry.get_agent(task.agent_name)
            
            # Step 2: Invoke agent with retry logic
            log_event(
                logger, 'info', 'agent_invoke_start',
                f"Invoking agent '{task.agent_name}' with retry logic",
                agent_name=task.agent_name,
                task_id=task.task_id,
                run_id=task.run_id,
                correlation_id=task.correlation_id,
                max_retries=agent_metadata.retry_config.max_retries
            )
            
            response_data = await self.retry_with_backoff(
                operation=lambda: self.invoke_agent(agent_metadata, task),
                retry_config=agent_metadata.retry_config,
                agent_name=task.agent_name,
                task_id=task.task_id
            )
            
            # Step 3: Handle successful response
            await self._handle_success_response(task, response_data)
            
        except Exception as e:
            # Step 4: Handle error response
            await self._handle_error_response(task, e)
    
    async def _handle_success_response(
        self,
        task: AgentTask,
        response_data: Dict[str, Any]
    ) -> None:
        """
        Handle a successful agent response.
        
        Extracts output data from the response and publishes a success result.
        
        Args:
            task: The original agent task
            response_data: The parsed JSON response from the agent
        """
        try:
            # Extract output data from A2A response format
            # Expected format: {"task_id": "...", "status": "success", "output": {...}}
            output_data = response_data.get('output', {})
            response_status = response_data.get('status', 'success').lower()
            
            # Check if agent reported an error in the response
            if response_status == 'error':
                error_message = response_data.get('error', 'Agent reported error status')
                logger.warning(
                    f"Agent '{task.agent_name}' returned error status",
                    extra={
                        'agent_name': task.agent_name,
                        'task_id': task.task_id,
                        'error_message': error_message
                    }
                )
                
                # Publish failure result
                result = AgentResult(
                    run_id=task.run_id,
                    task_id=task.task_id,
                    status='FAILURE',
                    output_data=None,
                    correlation_id=task.correlation_id,
                    error_message=error_message
                )
            else:
                # Publish success result
                log_event(
                    logger, 'info', 'agent_success',
                    f"Agent '{task.agent_name}' completed successfully",
                    agent_name=task.agent_name,
                    task_id=task.task_id,
                    run_id=task.run_id,
                    correlation_id=task.correlation_id
                )
                
                result = AgentResult(
                    run_id=task.run_id,
                    task_id=task.task_id,
                    status='SUCCESS',
                    output_data=output_data,
                    correlation_id=task.correlation_id,
                    error_message=None
                )
            
            # Publish result to Kafka
            await self._publish_result(result)
            
        except Exception as e:
            logger.error(
                f"Error handling success response for task '{task.task_id}': {e}",
                extra={
                    'task_id': task.task_id,
                    'agent_name': task.agent_name,
                    'error': str(e)
                }
            )
            
            # Publish failure result due to malformed response
            result = AgentResult(
                run_id=task.run_id,
                task_id=task.task_id,
                status='FAILURE',
                output_data=None,
                correlation_id=task.correlation_id,
                error_message=f"Malformed agent response: {str(e)}"
            )
            await self._publish_result(result)
    
    async def _handle_error_response(
        self,
        task: AgentTask,
        error: Exception
    ) -> None:
        """
        Handle an error during agent invocation.
        
        Creates and publishes a failure result with error details.
        
        Args:
            task: The original agent task
            error: The exception that occurred
        """
        log_event(
            logger, 'error', 'agent_error',
            f"Agent '{task.agent_name}' invocation failed: {error}",
            agent_name=task.agent_name,
            task_id=task.task_id,
            run_id=task.run_id,
            correlation_id=task.correlation_id,
            error=str(error),
            error_type=type(error).__name__
        )
        
        # Extract error details
        error_message = str(error)
        
        # Add HTTP status code if available
        if isinstance(error, httpx.HTTPStatusError):
            error_message = f"HTTP {error.response.status_code}: {error_message}"
        
        # Create failure result
        result = AgentResult(
            run_id=task.run_id,
            task_id=task.task_id,
            status='FAILURE',
            output_data=None,
            correlation_id=task.correlation_id,
            error_message=error_message
        )
        
        # Publish result to Kafka
        await self._publish_result(result)
    
    async def _publish_result(self, result: AgentResult) -> None:
        """
        Publish an agent result to Kafka.
        
        Args:
            result: The agent result to publish
        """
        try:
            # Convert result to dictionary for Kafka
            result_dict = result.model_dump()
            
            logger.info(
                f"Publishing result for task '{result.task_id}' with status '{result.status}'",
                extra={
                    'task_id': result.task_id,
                    'run_id': result.run_id,
                    'status': result.status,
                    'correlation_id': result.correlation_id
                }
            )
            
            # Publish to results topic
            await self.kafka_producer.publish(
                topic=self.results_topic,
                message=result_dict,
                key=result.correlation_id
            )
            
            logger.info(
                f"Successfully published result for task '{result.task_id}'",
                extra={
                    'task_id': result.task_id,
                    'run_id': result.run_id,
                    'status': result.status
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to publish result for task '{result.task_id}': {e}",
                extra={
                    'task_id': result.task_id,
                    'run_id': result.run_id,
                    'error': str(e)
                }
            )
            # Don't raise - we've already logged the error
            # The task will timeout on the executor side
    
    def _extract_output_from_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract output from JSON-RPC result.
        
        Extracts text from artifacts and history to create output, while preserving
        the full result structure for downstream processing.
        
        Args:
            result: JSON-RPC result object
            
        Returns:
            Extracted output dictionary with both structured and text data
        """
        output = {}
        
        # Always include the full result for complete data access
        # This ensures that agents returning structured data don't lose information
        output.update(result)
        
        # Extract from artifacts for backward compatibility
        artifacts = result.get('artifacts', [])
        if artifacts:
            artifact_texts = []
            for artifact in artifacts:
                parts = artifact.get('parts', [])
                for part in parts:
                    if part.get('kind') == 'text':
                        artifact_texts.append(part.get('text', ''))
            
            if artifact_texts:
                output['text'] = '\n'.join(artifact_texts)
                # Keep artifacts as they may contain structured data
                output['artifacts'] = artifacts
        
        # Extract from history (last agent message) for backward compatibility
        history = result.get('history', [])
        for item in reversed(history):
            if item.get('role') == 'agent':
                parts = item.get('parts', [])
                for part in parts:
                    if part.get('kind') == 'text':
                        output['response'] = part.get('text', '')
                        break
                if 'response' in output:
                    break
        
        # Ensure metadata is preserved
        if 'metadata' in result:
            output['metadata'] = result['metadata']
        
        # Ensure context ID is preserved
        if 'contextId' in result:
            output['context_id'] = result['contextId']
        
        # Ensure task ID is preserved
        if 'id' in result:
            output['task_id'] = result['id']
        
        return output
    
    def _parse_jsonrpc_response(
        self, 
        response: Dict[str, Any], 
        task_id: str
    ) -> Dict[str, Any]:
        """
        Parse JSON-RPC 2.0 response and convert to internal format.
        
        Args:
            response: JSON-RPC response from agent
            task_id: Original task ID for correlation
            
        Returns:
            Response in internal format: {task_id, status, output, error}
            
        Raises:
            ValueError: If response is malformed
        """
        # Validate JSON-RPC structure
        if 'jsonrpc' not in response:
            raise ValueError("Response missing 'jsonrpc' field")
        
        if response['jsonrpc'] != '2.0':
            raise ValueError(
                f"Unsupported JSON-RPC version: {response['jsonrpc']}"
            )
        
        # Check for error response
        if 'error' in response:
            error_obj = response['error']
            error_code = error_obj.get('code', 'unknown')
            error_message = error_obj.get('message', 'Unknown error')
            
            logger.error(
                f"JSON-RPC error response: {error_code} - {error_message}",
                extra={
                    'task_id': task_id,
                    'error_code': error_code,
                    'error_message': error_message,
                    'error_data': error_obj.get('data')
                }
            )
            
            return {
                'task_id': task_id,
                'status': 'error',
                'output': None,
                'error': f"JSON-RPC Error {error_code}: {error_message}"
            }
        
        # Process success response
        if 'result' not in response:
            raise ValueError("Response missing both 'result' and 'error'")
        
        result = response['result']
        
        # Extract status
        status_obj = result.get('status', {})
        state = status_obj.get('state', 'unknown')
        
        if state == 'completed':
            status = 'success'
            error = None
        else:
            status = 'error'
            error = f"Task state: {state}"
            logger.warning(
                f"Task completed with non-completed state: {state}",
                extra={'task_id': task_id, 'state': state}
            )
        
        # Extract output
        try:
            output = self._extract_output_from_result(result)
        except Exception as e:
            logger.error(
                f"Failed to extract output from result: {e}",
                extra={'task_id': task_id, 'result': result}
            )
            # Return full result as fallback
            output = result
        
        return {
            'task_id': task_id,
            'status': status,
            'output': output,
            'error': error
        }
    
    def _convert_input_to_message_parts(self, input_data: Any) -> list:
        """
        Convert task input data to JSON-RPC message parts.
        
        Args:
            input_data: Task input data (dict, string, or other)
            
        Returns:
            List of message parts with 'kind' and 'text' fields
        """
        parts = []
        
        if isinstance(input_data, dict):
            # Check for common text fields
            text_content = input_data.get('text') or input_data.get('query')
            if text_content:
                parts.append({
                    'kind': 'text',
                    'text': str(text_content)
                })
            else:
                # Serialize entire dict as JSON
                import json
                parts.append({
                    'kind': 'text',
                    'text': json.dumps(input_data)
                })
        else:
            # Convert to string
            parts.append({
                'kind': 'text',
                'text': str(input_data)
            })
        
        return parts
    
    def _build_jsonrpc_request(self, task: AgentTask) -> Dict[str, Any]:
        """
        Build a JSON-RPC 2.0 request from a task.
        
        Args:
            task: The agent task
            
        Returns:
            JSON-RPC 2.0 formatted request
        """
        return {
            'jsonrpc': '2.0',
            'id': task.task_id,
            'method': 'message/send',
            'params': {
                'message': {
                    'role': 'user',
                    'messageId': f"msg-{task.task_id}",
                    'parts': self._convert_input_to_message_parts(task.input_data)
                }
            }
        }
    
    async def invoke_agent(
        self,
        agent_metadata: AgentMetadata,
        task: AgentTask
    ) -> Dict[str, Any]:
        """
        Invoke an external agent via HTTP using JSON-RPC 2.0 protocol.
        
        Constructs a JSON-RPC 2.0 HTTP POST request and makes the call
        to the agent endpoint with appropriate authentication.
        Uses circuit breaker to prevent calls to failing agents.
        
        Args:
            agent_metadata: Metadata about the agent including URL and auth config
            task: The agent task containing input data
            
        Returns:
            The parsed response in internal format
            
        Raises:
            httpx.HTTPError: If the HTTP request fails
            CircuitBreakerOpenError: If circuit breaker is open
        """
        # Get circuit breaker for this agent
        circuit_breaker_config = None
        if agent_metadata.circuit_breaker_config:
            # Convert Pydantic model to dataclass
            circuit_breaker_config = CircuitBreakerConfig(
                enabled=agent_metadata.circuit_breaker_config.enabled,
                failure_threshold=agent_metadata.circuit_breaker_config.failure_threshold,
                failure_rate_threshold=agent_metadata.circuit_breaker_config.failure_rate_threshold,
                timeout_seconds=agent_metadata.circuit_breaker_config.timeout_seconds,
                half_open_max_calls=agent_metadata.circuit_breaker_config.half_open_max_calls,
                window_size_seconds=agent_metadata.circuit_breaker_config.window_size_seconds
            )
        
        circuit_breaker = self.circuit_breaker_manager.get_circuit_breaker(
            agent_name=agent_metadata.name,
            config=circuit_breaker_config
        )
        
        # Execute through circuit breaker
        try:
            return await circuit_breaker.call(
                lambda: self._invoke_agent_http(agent_metadata, task)
            )
        except CircuitBreakerOpenError as e:
            # Circuit is open, fail immediately
            log_event(
                logger, 'warning', 'circuit_breaker_open',
                f"Circuit breaker open for agent '{agent_metadata.name}'",
                agent_name=agent_metadata.name,
                task_id=task.task_id,
                run_id=task.run_id,
                correlation_id=task.correlation_id
            )
            raise
    
    async def _invoke_agent_http(
        self,
        agent_metadata: AgentMetadata,
        task: AgentTask
    ) -> Dict[str, Any]:
        """
        Internal method to invoke agent via HTTP.
        
        This method is called by the circuit breaker.
        
        Args:
            agent_metadata: Metadata about the agent including URL and auth config
            task: The agent task containing input data
            
        Returns:
            The parsed response in internal format
            
        Raises:
            httpx.HTTPError: If the HTTP request fails
        """
        log_event(
            logger, 'info', 'http_call',
            f"Invoking agent '{agent_metadata.name}' at {agent_metadata.url} using JSON-RPC 2.0",
            agent_name=agent_metadata.name,
            agent_url=agent_metadata.url,
            task_id=task.task_id,
            run_id=task.run_id,
            correlation_id=task.correlation_id
        )
        
        # Construct JSON-RPC 2.0 request payload
        request_payload = self._build_jsonrpc_request(task)
        
        logger.debug(
            f"JSON-RPC request for task {task.task_id}",
            extra={
                'task_id': task.task_id,
                'agent_name': agent_metadata.name,
                'request': request_payload
            }
        )
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Correlation-ID': task.correlation_id
        }
        
        # Add authentication headers if configured
        if agent_metadata.auth_config:
            auth_type = agent_metadata.auth_config.get('type', '').lower()
            
            if auth_type == 'bearer':
                token = agent_metadata.auth_config.get('token')
                if token:
                    headers['Authorization'] = f'Bearer {token}'
                    logger.debug(f"Added Bearer token authentication for agent '{agent_metadata.name}'")
            
            elif auth_type == 'apikey':
                api_key = agent_metadata.auth_config.get('key')
                header_name = agent_metadata.auth_config.get('header', 'X-API-Key')
                if api_key:
                    headers[header_name] = api_key
                    logger.debug(f"Added API key authentication for agent '{agent_metadata.name}'")
            
            else:
                logger.warning(
                    f"Unknown authentication type '{auth_type}' for agent '{agent_metadata.name}'"
                )
        
        # Use agent-specific timeout if configured
        timeout = agent_metadata.timeout / 1000.0  # Convert ms to seconds
        
        # Make HTTP POST request
        try:
            response = await self.http_client.post(
                agent_metadata.url,
                json=request_payload,
                headers=headers,
                timeout=timeout
            )
            
            # Raise for error status codes
            response.raise_for_status()
            
            # Parse JSON response
            response_data = response.json()
            
            logger.debug(
                f"JSON-RPC response for task {task.task_id}",
                extra={
                    'task_id': task.task_id,
                    'agent_name': agent_metadata.name,
                    'response': response_data
                }
            )
            
            # Parse JSON-RPC response and convert to internal format
            result = self._parse_jsonrpc_response(response_data, task.task_id)
            
            log_event(
                logger, 'info', 'http_success',
                f"Successfully invoked agent '{agent_metadata.name}'",
                agent_name=agent_metadata.name,
                task_id=task.task_id,
                run_id=task.run_id,
                status_code=response.status_code,
                result_status=result.get('status'),
                correlation_id=task.correlation_id
            )
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Agent '{agent_metadata.name}' returned error status {e.response.status_code}",
                extra={
                    'agent_name': agent_metadata.name,
                    'task_id': task.task_id,
                    'status_code': e.response.status_code,
                    'error': str(e)
                }
            )
            raise
        
        except httpx.TimeoutException as e:
            logger.error(
                f"Timeout invoking agent '{agent_metadata.name}' after {timeout}s",
                extra={
                    'agent_name': agent_metadata.name,
                    'task_id': task.task_id,
                    'timeout': timeout,
                    'error': str(e)
                }
            )
            raise
        
        except Exception as e:
            logger.error(
                f"Error invoking agent '{agent_metadata.name}': {e}",
                extra={
                    'agent_name': agent_metadata.name,
                    'task_id': task.task_id,
                    'error': str(e)
                }
            )
            raise

    async def retry_with_backoff(
        self,
        operation,
        retry_config: RetryConfig,
        agent_name: str,
        task_id: str
    ) -> Any:
        """
        Execute an operation with exponential backoff retry logic.
        
        Retries the operation on retriable errors (network errors, 5xx status codes)
        with exponentially increasing delays between attempts.
        
        Args:
            operation: Async callable to execute
            retry_config: Retry configuration with max attempts and delay settings
            agent_name: Name of the agent (for logging)
            task_id: Task ID (for logging)
            
        Returns:
            The result of the operation if successful
            
        Raises:
            Exception: The last error encountered if all retries fail
        """
        attempt = 0
        delay = retry_config.initial_delay_ms / 1000.0  # Convert to seconds
        last_error = None
        
        while attempt < retry_config.max_retries:
            try:
                # Execute the operation
                result = await operation()
                
                # Log success if this was a retry
                if attempt > 0:
                    logger.info(
                        f"Operation succeeded on attempt {attempt + 1} for agent '{agent_name}'",
                        extra={
                            'agent_name': agent_name,
                            'task_id': task_id,
                            'attempt': attempt + 1
                        }
                    )
                
                return result
                
            except Exception as error:
                last_error = error
                attempt += 1
                
                # Check if error is retriable
                is_retriable = self._is_retriable_error(error)
                
                # If not retriable or last attempt, raise immediately
                if not is_retriable or attempt >= retry_config.max_retries:
                    logger.error(
                        f"Operation failed for agent '{agent_name}' after {attempt} attempt(s): {error}",
                        extra={
                            'agent_name': agent_name,
                            'task_id': task_id,
                            'attempt': attempt,
                            'is_retriable': is_retriable,
                            'error': str(error)
                        }
                    )
                    raise error
                
                # Log retry attempt
                logger.warning(
                    f"Attempt {attempt}/{retry_config.max_retries} failed for agent '{agent_name}': "
                    f"{error}. Retrying in {delay:.2f}s...",
                    extra={
                        'agent_name': agent_name,
                        'task_id': task_id,
                        'attempt': attempt,
                        'delay_seconds': delay,
                        'error': str(error)
                    }
                )
                
                # Wait before retry
                await asyncio.sleep(delay)
                
                # Calculate next delay with exponential backoff
                delay = min(
                    delay * retry_config.backoff_multiplier,
                    retry_config.max_delay_ms / 1000.0
                )
        
        # Should not reach here, but just in case
        raise last_error or Exception(f"Operation failed after {retry_config.max_retries} attempts")
    
    def _is_retriable_error(self, error: Exception) -> bool:
        """
        Determine if an error is retriable.
        
        Retriable errors include:
        - Network errors (connection failures, timeouts)
        - 5xx server errors
        - 429 Too Many Requests
        
        Non-retriable errors include:
        - 4xx client errors (except 429)
        - Invalid response format
        
        Args:
            error: The exception to check
            
        Returns:
            True if the error is retriable, False otherwise
        """
        # Network errors are retriable
        if isinstance(error, (httpx.NetworkError, httpx.TimeoutException)):
            logger.debug(f"Error is retriable: {type(error).__name__}")
            return True
        
        # HTTP status errors
        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
            
            # 5xx errors are retriable
            if 500 <= status_code < 600:
                logger.debug(f"Error is retriable: HTTP {status_code}")
                return True
            
            # 429 Too Many Requests is retriable
            if status_code == 429:
                logger.debug(f"Error is retriable: HTTP 429 Too Many Requests")
                return True
            
            # Other 4xx errors are not retriable
            logger.debug(f"Error is not retriable: HTTP {status_code}")
            return False
        
        # Other errors (like ValueError, JSON decode errors) are not retriable
        logger.debug(f"Error is not retriable: {type(error).__name__}")
        return False
