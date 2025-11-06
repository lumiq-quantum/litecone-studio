"""Kafka consumer wrapper with async support."""

import asyncio
import logging
import json
from typing import Optional, Dict, Any, Callable, Awaitable, List
from kafka import KafkaConsumer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class KafkaConsumerClient:
    """Async wrapper for Kafka consumer with message deserialization and filtering."""
    
    def __init__(
        self,
        topics: List[str],
        bootstrap_servers: str,
        group_id: str,
        client_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Kafka consumer client.
        
        Args:
            topics: List of Kafka topics to subscribe to
            bootstrap_servers: Comma-separated list of Kafka broker addresses
            group_id: Consumer group ID for coordinated consumption
            client_id: Optional client identifier for the consumer
            **kwargs: Additional configuration options for KafkaConsumer
        """
        self.topics = topics
        self.bootstrap_servers = bootstrap_servers.split(',')
        self.group_id = group_id
        self.client_id = client_id or 'kafka-consumer-client'
        self._consumer: Optional[KafkaConsumer] = None
        self._additional_config = kwargs
        self._running = False
        
        logger.info(
            "Initializing KafkaConsumerClient",
            extra={
                'topics': self.topics,
                'bootstrap_servers': self.bootstrap_servers,
                'group_id': self.group_id,
                'client_id': self.client_id
            }
        )
    
    def connect(self) -> None:
        """Establish connection to Kafka brokers and subscribe to topics."""
        try:
            self._consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                client_id=self.client_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                **self._additional_config
            )
            logger.info(
                f"Successfully connected to Kafka brokers and subscribed to topics: {self.topics}"
            )
        except KafkaError as e:
            logger.error(
                f"Failed to connect to Kafka brokers: {e}",
                extra={'error': str(e)}
            )
            raise
    
    async def consume(
        self,
        message_handler: Callable[[Dict[str, Any]], Awaitable[None]],
        correlation_id_filter: Optional[str] = None,
        timeout_ms: int = 1000
    ) -> None:
        """
        Consume messages from subscribed topics asynchronously.
        
        Args:
            message_handler: Async callback function to process each message
            correlation_id_filter: Optional correlation ID to filter messages
            timeout_ms: Polling timeout in milliseconds
            
        Raises:
            RuntimeError: If consumer is not connected
        """
        if self._consumer is None:
            raise RuntimeError("Consumer not connected. Call connect() first.")
        
        self._running = True
        logger.info(
            "Starting message consumption",
            extra={
                'correlation_id_filter': correlation_id_filter,
                'timeout_ms': timeout_ms
            }
        )
        
        try:
            while self._running:
                # Poll for messages in a non-blocking way
                messages = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._consumer.poll(timeout_ms=timeout_ms)
                )
                
                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            message = record.value
                            
                            # Apply correlation ID filtering if specified
                            if correlation_id_filter:
                                message_correlation_id = message.get('correlation_id')
                                if message_correlation_id != correlation_id_filter:
                                    logger.debug(
                                        f"Skipping message with correlation_id '{message_correlation_id}' "
                                        f"(looking for '{correlation_id_filter}')"
                                    )
                                    continue
                            
                            logger.debug(
                                f"Received message from topic '{topic_partition.topic}'",
                                extra={
                                    'topic': topic_partition.topic,
                                    'partition': topic_partition.partition,
                                    'offset': record.offset,
                                    'key': record.key
                                }
                            )
                            
                            # Process message with the handler
                            await message_handler(message)
                            
                        except Exception as e:
                            logger.error(
                                f"Error processing message: {e}",
                                extra={
                                    'topic': topic_partition.topic,
                                    'partition': topic_partition.partition,
                                    'offset': record.offset,
                                    'error': str(e)
                                }
                            )
                            # Continue processing other messages
                
                # Yield control to allow other tasks to run
                await asyncio.sleep(0)
                
        except Exception as e:
            logger.error(f"Error in consume loop: {e}", extra={'error': str(e)})
            raise
        finally:
            logger.info("Message consumption stopped")
    
    async def consume_one(
        self,
        correlation_id_filter: Optional[str] = None,
        timeout_seconds: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Consume a single message matching the correlation ID filter.
        
        Args:
            correlation_id_filter: Optional correlation ID to filter messages
            timeout_seconds: Maximum time to wait for a matching message
            
        Returns:
            The first matching message, or None if timeout is reached
            
        Raises:
            RuntimeError: If consumer is not connected
        """
        if self._consumer is None:
            raise RuntimeError("Consumer not connected. Call connect() first.")
        
        logger.info(
            "Waiting for single message",
            extra={
                'correlation_id_filter': correlation_id_filter,
                'timeout_seconds': timeout_seconds
            }
        )
        
        start_time = asyncio.get_event_loop().time()
        timeout_ms = 1000
        
        try:
            while True:
                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= timeout_seconds:
                    logger.warning(
                        f"Timeout waiting for message with correlation_id '{correlation_id_filter}'"
                    )
                    return None
                
                # Poll for messages
                messages = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._consumer.poll(timeout_ms=timeout_ms)
                )
                
                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            message = record.value
                            
                            # Apply correlation ID filtering if specified
                            if correlation_id_filter:
                                message_correlation_id = message.get('correlation_id')
                                if message_correlation_id != correlation_id_filter:
                                    continue
                            
                            logger.info(
                                f"Found matching message from topic '{topic_partition.topic}'",
                                extra={
                                    'topic': topic_partition.topic,
                                    'partition': topic_partition.partition,
                                    'offset': record.offset,
                                    'correlation_id': correlation_id_filter
                                }
                            )
                            
                            return message
                            
                        except Exception as e:
                            logger.error(
                                f"Error processing message: {e}",
                                extra={'error': str(e)}
                            )
                
                # Yield control to allow other tasks to run
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in consume_one: {e}", extra={'error': str(e)})
            raise
    
    def stop(self) -> None:
        """Stop the consumer loop."""
        self._running = False
        logger.info("Consumer stop requested")
    
    def close(self) -> None:
        """Close the Kafka consumer connection."""
        self.stop()
        if self._consumer:
            try:
                self._consumer.close()
                logger.info("Kafka consumer connection closed")
            except Exception as e:
                logger.error(f"Error closing Kafka consumer: {e}")
            finally:
                self._consumer = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
