"""
Execution Consumer Service

This service consumes workflow execution requests from Kafka and spawns
executor instances to process them. It bridges the API and the executor.

Requirements:
- 11.1: Consume execution requests from API-published Kafka messages
- 11.2: Update run status in database when executor completes
- 11.5: Queue execution requests when executor is unavailable
"""

import asyncio
import logging
import json
import signal
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

from src.kafka_client.consumer import KafkaConsumerClient
from src.executor.centralized_executor import CentralizedExecutor
from src.models.workflow import WorkflowPlan
from src.utils.logging import setup_logging, log_event

logger = logging.getLogger(__name__)


class ExecutionConsumer:
    """
    Consumer service that listens for workflow execution requests and spawns executors.
    
    This service:
    1. Consumes messages from workflow.execution.requests topic
    2. Validates and parses execution requests
    3. Spawns CentralizedExecutor instances to process workflows
    4. Handles graceful shutdown
    """
    
    def __init__(
        self,
        kafka_bootstrap_servers: str,
        kafka_group_id: str,
        database_url: str,
        agent_registry_url: str,
        execution_topic: str = "workflow.execution.requests",
        cancellation_topic: str = "workflow.cancellation.requests"
    ):
        """
        Initialize the Execution Consumer.
        
        Args:
            kafka_bootstrap_servers: Comma-separated Kafka broker addresses
            kafka_group_id: Kafka consumer group ID
            database_url: PostgreSQL connection URL
            agent_registry_url: Agent Registry service URL
            execution_topic: Kafka topic for execution requests
            cancellation_topic: Kafka topic for cancellation requests
        """
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_group_id = kafka_group_id
        self.database_url = database_url
        self.agent_registry_url = agent_registry_url
        self.execution_topic = execution_topic
        self.cancellation_topic = cancellation_topic
        
        self.consumer: Optional[KafkaConsumerClient] = None
        self.running = False
        self.active_executors: Dict[str, asyncio.Task] = {}
        
        logger.info(
            "Initialized ExecutionConsumer",
            extra={
                "execution_topic": execution_topic,
                "cancellation_topic": cancellation_topic,
                "kafka_group_id": kafka_group_id
            }
        )
    
    async def initialize(self) -> None:
        """Initialize Kafka consumer connection."""
        logger.info("Initializing Kafka consumer")
        
        self.consumer = KafkaConsumerClient(
            topics=[self.execution_topic, self.cancellation_topic],
            bootstrap_servers=self.kafka_bootstrap_servers,
            group_id=self.kafka_group_id,
            client_id=f"execution-consumer-{self.kafka_group_id}"
        )
        self.consumer.connect()
        
        logger.info("Kafka consumer initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown consumer and wait for active executors to complete."""
        logger.info("Shutting down ExecutionConsumer")
        
        self.running = False
        
        # Wait for active executors to complete (with timeout)
        if self.active_executors:
            logger.info(f"Waiting for {len(self.active_executors)} active executors to complete")
            
            # Give executors 30 seconds to complete gracefully
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.active_executors.values(), return_exceptions=True),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for executors to complete, cancelling remaining tasks")
                for run_id, task in self.active_executors.items():
                    if not task.done():
                        logger.warning(f"Cancelling executor for run_id={run_id}")
                        task.cancel()
        
        # Close Kafka consumer
        if self.consumer:
            try:
                self.consumer.close()
                logger.info("Kafka consumer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka consumer: {e}")
        
        logger.info("ExecutionConsumer shutdown complete")
    
    async def process_execution_request(self, message: Dict[str, Any]) -> None:
        """
        Process a workflow execution request message.
        
        Args:
            message: Execution request message containing run_id, workflow_plan, and input_data
        """
        run_id = message.get("run_id")
        if not run_id:
            logger.error("Received execution request without run_id", extra={"message": message})
            return
        
        log_event(
            logger, 'info', 'execution_request_received',
            f"Received execution request for run_id={run_id}",
            run_id=run_id
        )
        
        try:
            # Extract workflow plan and input data
            workflow_plan_dict = message.get("workflow_plan")
            input_data = message.get("input_data", {})
            
            if not workflow_plan_dict:
                logger.error(
                    f"Execution request missing workflow_plan",
                    extra={"run_id": run_id}
                )
                return
            
            # Validate and parse workflow plan
            workflow_plan = WorkflowPlan(**workflow_plan_dict)
            
            log_event(
                logger, 'info', 'spawning_executor',
                f"Spawning executor for run_id={run_id}",
                run_id=run_id,
                workflow_name=workflow_plan.name,
                workflow_version=workflow_plan.version
            )
            
            # Spawn executor task
            task = asyncio.create_task(
                self._execute_workflow(run_id, workflow_plan, input_data)
            )
            self.active_executors[run_id] = task
            
            # Add callback to remove from active executors when done
            task.add_done_callback(lambda t: self._executor_completed(run_id, t))
            
        except Exception as e:
            logger.error(
                f"Failed to process execution request for run_id={run_id}: {e}",
                extra={"run_id": run_id, "error": str(e)},
                exc_info=True
            )
    
    async def process_cancellation_request(self, message: Dict[str, Any]) -> None:
        """
        Process a workflow cancellation request message.
        
        Args:
            message: Cancellation request message containing run_id
        """
        run_id = message.get("run_id")
        if not run_id:
            logger.error("Received cancellation request without run_id", extra={"message": message})
            return
        
        log_event(
            logger, 'info', 'cancellation_request_received',
            f"Received cancellation request for run_id={run_id}",
            run_id=run_id,
            cancelled_by=message.get("cancelled_by"),
            reason=message.get("reason")
        )
        
        # Check if executor is running for this run_id
        if run_id in self.active_executors:
            task = self.active_executors[run_id]
            if not task.done():
                logger.info(f"Cancelling executor for run_id={run_id}")
                task.cancel()
            else:
                logger.info(f"Executor for run_id={run_id} already completed")
        else:
            logger.info(f"No active executor found for run_id={run_id}")
    
    async def _execute_workflow(
        self,
        run_id: str,
        workflow_plan: WorkflowPlan,
        input_data: Dict[str, Any]
    ) -> None:
        """
        Execute a workflow using CentralizedExecutor.
        
        Args:
            run_id: Unique identifier for the workflow run
            workflow_plan: Parsed workflow plan
            input_data: Initial input data for the workflow
        """
        executor = None
        
        try:
            log_event(
                logger, 'info', 'executor_starting',
                f"Starting executor for run_id={run_id}",
                run_id=run_id,
                workflow_name=workflow_plan.name
            )
            
            # Create executor instance
            executor = CentralizedExecutor(
                run_id=run_id,
                workflow_plan=workflow_plan,
                initial_input=input_data,
                kafka_bootstrap_servers=self.kafka_bootstrap_servers,
                database_url=self.database_url,
                agent_registry_url=self.agent_registry_url
            )
            
            # Initialize executor
            await executor.initialize()
            
            # Load any existing execution state for replay
            await executor.load_execution_state()
            
            # Execute workflow
            await executor.execute_workflow()
            
            log_event(
                logger, 'info', 'executor_completed',
                f"Executor completed successfully for run_id={run_id}",
                run_id=run_id,
                workflow_name=workflow_plan.name
            )
            
        except asyncio.CancelledError:
            log_event(
                logger, 'warning', 'executor_cancelled',
                f"Executor cancelled for run_id={run_id}",
                run_id=run_id
            )
            raise
        except Exception as e:
            log_event(
                logger, 'error', 'executor_failed',
                f"Executor failed for run_id={run_id}: {e}",
                run_id=run_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
        finally:
            # Shutdown executor
            if executor:
                try:
                    await executor.shutdown()
                except Exception as e:
                    logger.error(
                        f"Error shutting down executor for run_id={run_id}: {e}",
                        extra={"run_id": run_id}
                    )
    
    def _executor_completed(self, run_id: str, task: asyncio.Task) -> None:
        """
        Callback when executor task completes.
        
        Args:
            run_id: Run identifier
            task: Completed task
        """
        # Remove from active executors
        if run_id in self.active_executors:
            del self.active_executors[run_id]
        
        # Check for exceptions
        if not task.cancelled():
            try:
                task.result()
            except Exception as e:
                logger.error(
                    f"Executor task failed for run_id={run_id}: {e}",
                    extra={"run_id": run_id, "error": str(e)}
                )
    
    async def run(self) -> None:
        """
        Main consumer loop that processes execution and cancellation requests.
        """
        logger.info("Starting ExecutionConsumer main loop")
        self.running = True
        
        while self.running:
            try:
                # Consume messages with timeout
                message = await self.consumer.consume_one(timeout_seconds=1.0)
                
                if message is None:
                    # Timeout, continue loop
                    continue
                
                # Determine message type based on topic or message_type field
                message_type = message.get("message_type")
                
                if message_type == "execution_request":
                    await self.process_execution_request(message)
                elif message_type == "cancellation_request":
                    await self.process_cancellation_request(message)
                else:
                    # Try to infer from message structure
                    if "workflow_plan" in message:
                        await self.process_execution_request(message)
                    elif "cancelled_by" in message or "reason" in message:
                        await self.process_cancellation_request(message)
                    else:
                        logger.warning(
                            "Received message with unknown type",
                            extra={"message": message}
                        )
                
            except asyncio.CancelledError:
                logger.info("Consumer loop cancelled")
                break
            except Exception as e:
                logger.error(
                    f"Error in consumer loop: {e}",
                    extra={"error": str(e)},
                    exc_info=True
                )
                # Sleep briefly to avoid tight loop on persistent errors
                await asyncio.sleep(1.0)
        
        logger.info("ExecutionConsumer main loop stopped")


# Global consumer instance for signal handling
_consumer_instance: Optional[ExecutionConsumer] = None
_shutdown_event = asyncio.Event()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    signal_name = signal.Signals(signum).name
    logger.info(f"Received signal {signal_name}, initiating graceful shutdown...")
    _shutdown_event.set()


async def main():
    """
    Main entry point for the Execution Consumer service.
    
    Environment Variables:
        KAFKA_BROKERS: Comma-separated Kafka broker addresses (required)
        KAFKA_GROUP_ID: Kafka consumer group ID (default: execution-consumer-group)
        DATABASE_URL: PostgreSQL connection URL (required)
        AGENT_REGISTRY_URL: Agent Registry service URL (required)
        KAFKA_EXECUTION_TOPIC: Execution requests topic (default: workflow.execution.requests)
        KAFKA_CANCELLATION_TOPIC: Cancellation requests topic (default: workflow.cancellation.requests)
        LOG_LEVEL: Logging level (default: INFO)
        LOG_FORMAT: Log format ('json' or 'text', default: json)
    """
    global _consumer_instance
    
    # Configure structured logging
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = os.getenv('LOG_FORMAT', 'json').lower()
    setup_logging(log_level=log_level, log_format=log_format)
    
    log_event(
        logger, 'info', 'consumer_start',
        "Starting Execution Consumer Service",
        log_level=log_level,
        log_format=log_format
    )
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Load configuration from environment
        kafka_brokers = os.getenv('KAFKA_BROKERS')
        if not kafka_brokers:
            raise ValueError("KAFKA_BROKERS environment variable is required")
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        agent_registry_url = os.getenv('AGENT_REGISTRY_URL')
        if not agent_registry_url:
            raise ValueError("AGENT_REGISTRY_URL environment variable is required")
        
        kafka_group_id = os.getenv('KAFKA_GROUP_ID', 'execution-consumer-group')
        execution_topic = os.getenv('KAFKA_EXECUTION_TOPIC', 'workflow.execution.requests')
        cancellation_topic = os.getenv('KAFKA_CANCELLATION_TOPIC', 'workflow.cancellation.requests')
        
        log_event(
            logger, 'info', 'config_loaded',
            "Configuration loaded",
            kafka_brokers=kafka_brokers,
            kafka_group_id=kafka_group_id,
            execution_topic=execution_topic,
            cancellation_topic=cancellation_topic
        )
        
        # Create consumer instance
        consumer = ExecutionConsumer(
            kafka_bootstrap_servers=kafka_brokers,
            kafka_group_id=kafka_group_id,
            database_url=database_url,
            agent_registry_url=agent_registry_url,
            execution_topic=execution_topic,
            cancellation_topic=cancellation_topic
        )
        _consumer_instance = consumer
        
        # Initialize consumer
        logger.info("Initializing consumer...")
        await consumer.initialize()
        
        # Create a task for consumer loop
        consumer_task = asyncio.create_task(consumer.run())
        
        # Wait for either consumer to complete or shutdown signal
        done, pending = await asyncio.wait(
            [consumer_task, asyncio.create_task(_shutdown_event.wait())],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Check if shutdown was requested
        if _shutdown_event.is_set():
            logger.info("Shutdown signal received")
            # Cancel the consumer task
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                logger.info("Consumer task cancelled")
        
        # Shutdown consumer
        logger.info("Shutting down consumer...")
        await consumer.shutdown()
        
        logger.info("Execution Consumer Service terminated successfully")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error in Execution Consumer Service: {e}", exc_info=True)
        
        # Try to shutdown gracefully
        if _consumer_instance:
            try:
                await _consumer_instance.shutdown()
            except Exception as shutdown_error:
                logger.error(f"Error during shutdown: {shutdown_error}")
        
        sys.exit(1)


if __name__ == "__main__":
    """Entry point when running as a script."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, exiting...")
        sys.exit(0)
