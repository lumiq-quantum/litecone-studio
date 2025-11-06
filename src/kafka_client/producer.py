"""Kafka producer wrapper with async support."""

import asyncio
import logging
import json
from typing import Optional, Dict, Any
from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class KafkaProducerClient:
    """Async wrapper for Kafka producer with message serialization and error handling."""
    
    def __init__(
        self,
        bootstrap_servers: str,
        client_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Kafka producer client.
        
        Args:
            bootstrap_servers: Comma-separated list of Kafka broker addresses
            client_id: Optional client identifier for the producer
            **kwargs: Additional configuration options for KafkaProducer
        """
        self.bootstrap_servers = bootstrap_servers.split(',')
        self.client_id = client_id or 'kafka-producer-client'
        self._producer: Optional[KafkaProducer] = None
        self._additional_config = kwargs
        
        logger.info(
            "Initializing KafkaProducerClient",
            extra={
                'bootstrap_servers': self.bootstrap_servers,
                'client_id': self.client_id
            }
        )
    
    def connect(self) -> None:
        """Establish connection to Kafka brokers."""
        try:
            self._producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,
                max_in_flight_requests_per_connection=1,  # Ensure ordering
                **self._additional_config
            )
            logger.info("Successfully connected to Kafka brokers")
        except KafkaError as e:
            logger.error(
                f"Failed to connect to Kafka brokers: {e}",
                extra={'error': str(e)}
            )
            raise
    
    async def publish(
        self,
        topic: str,
        message: Dict[str, Any],
        key: Optional[str] = None
    ) -> None:
        """
        Publish a message to a Kafka topic asynchronously.
        
        Args:
            topic: The Kafka topic to publish to
            message: The message payload as a dictionary
            key: Optional message key for partitioning
            
        Raises:
            RuntimeError: If producer is not connected
            KafkaError: If message publishing fails
        """
        if self._producer is None:
            raise RuntimeError("Producer not connected. Call connect() first.")
        
        try:
            # Run the synchronous send in a thread pool to avoid blocking
            future = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._producer.send(topic, value=message, key=key)
            )
            
            # Wait for the send to complete
            record_metadata = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: future.get(timeout=10)
            )
            
            logger.info(
                f"Successfully published message to topic '{topic}'",
                extra={
                    'topic': topic,
                    'partition': record_metadata.partition,
                    'offset': record_metadata.offset,
                    'key': key
                }
            )
            
        except KafkaError as e:
            logger.error(
                f"Failed to publish message to topic '{topic}': {e}",
                extra={
                    'topic': topic,
                    'key': key,
                    'error': str(e)
                }
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error publishing message to topic '{topic}': {e}",
                extra={
                    'topic': topic,
                    'key': key,
                    'error': str(e)
                }
            )
            raise
    
    def close(self) -> None:
        """Close the Kafka producer connection."""
        if self._producer:
            try:
                self._producer.flush()
                self._producer.close()
                logger.info("Kafka producer connection closed")
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")
            finally:
                self._producer = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
