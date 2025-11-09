"""Kafka service for publishing workflow execution and cancellation requests."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.kafka_client.producer import KafkaProducerClient
from api.config import settings

logger = logging.getLogger(__name__)


class KafkaService:
    """
    Service for publishing messages to Kafka topics.
    
    This service provides methods to publish workflow execution requests
    and cancellation requests to Kafka topics for consumption by the
    executor service.
    
    Requirements:
    - 3.1: Trigger workflow execution via Kafka
    - 3.3: Publish cancellation requests to Kafka
    - 11.1: Publish execution requests to Kafka for executor service
    - 11.2: Update run status when executor completes
    - 11.4: Notify executor service via Kafka when workflow is cancelled
    """
    
    def __init__(self, producer_client: Optional[KafkaProducerClient] = None):
        """
        Initialize KafkaService with a producer client.
        
        Args:
            producer_client: Optional KafkaProducerClient instance.
                           If not provided, a new one will be created.
        """
        self._producer_client = producer_client
        self._is_external_client = producer_client is not None
    
    def _get_producer(self) -> KafkaProducerClient:
        """
        Get or create the Kafka producer client.
        
        Returns:
            KafkaProducerClient instance
        """
        if self._producer_client is None:
            self._producer_client = KafkaProducerClient(
                bootstrap_servers=settings.kafka_brokers,
                client_id="workflow-management-api"
            )
            self._producer_client.connect()
        return self._producer_client
    
    async def publish_execution_request(
        self,
        run_id: str,
        workflow_plan: Dict[str, Any],
        input_data: Dict[str, Any],
        workflow_name: Optional[str] = None
    ) -> None:
        """
        Publish a workflow execution request to Kafka.
        
        This method publishes a message to the execution topic that will be
        consumed by the executor service to start workflow execution.
        
        Args:
            run_id: Unique identifier for the workflow run
            workflow_plan: Complete workflow definition including steps
            input_data: Initial input data for the workflow
            workflow_name: Optional workflow name for logging
        
        Raises:
            RuntimeError: If producer is not connected
            KafkaError: If message publishing fails
        
        Example:
            await kafka_service.publish_execution_request(
                run_id="run-123",
                workflow_plan={
                    "workflow_id": "wf-data-pipeline-1",
                    "name": "data-pipeline",
                    "version": "1",
                    "start_step": "extract",
                    "steps": {...}
                },
                input_data={"source": "s3://bucket/data.csv"},
                workflow_name="data-pipeline"
            )
        
        Requirements:
        - 3.1: Creates run record and triggers executor service
        - 11.1: Publishes execution request to Kafka for executor
        """
        producer = self._get_producer()
        
        message = {
            "run_id": run_id,
            "workflow_plan": workflow_plan,
            "input_data": input_data,
            "timestamp": datetime.utcnow().isoformat(),
            "message_type": "execution_request"
        }
        
        logger.info(
            f"Publishing execution request for run '{run_id}'",
            extra={
                "run_id": run_id,
                "workflow_name": workflow_name or workflow_plan.get("name"),
                "topic": settings.kafka_execution_topic
            }
        )
        
        try:
            await producer.publish(
                topic=settings.kafka_execution_topic,
                message=message,
                key=run_id
            )
            
            logger.info(
                f"Successfully published execution request for run '{run_id}'",
                extra={
                    "run_id": run_id,
                    "workflow_name": workflow_name or workflow_plan.get("name")
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to publish execution request for run '{run_id}': {e}",
                extra={
                    "run_id": run_id,
                    "workflow_name": workflow_name or workflow_plan.get("name"),
                    "error": str(e)
                }
            )
            raise
    
    async def publish_cancellation_request(
        self,
        run_id: str,
        cancelled_by: Optional[str] = None,
        reason: Optional[str] = None
    ) -> None:
        """
        Publish a workflow cancellation request to Kafka.
        
        This method publishes a message to the cancellation topic that will be
        consumed by the executor service to stop workflow execution.
        
        Args:
            run_id: Unique identifier for the workflow run to cancel
            cancelled_by: Identifier of the user cancelling the workflow
            reason: Optional reason for cancellation
        
        Raises:
            RuntimeError: If producer is not connected
            KafkaError: If message publishing fails
        
        Example:
            await kafka_service.publish_cancellation_request(
                run_id="run-123",
                cancelled_by="admin@example.com",
                reason="User requested cancellation"
            )
        
        Requirements:
        - 3.3: Publishes cancellation request via POST /api/v1/runs/{run_id}/cancel
        - 11.4: Notifies executor service via Kafka when workflow is cancelled
        """
        producer = self._get_producer()
        
        message = {
            "run_id": run_id,
            "cancelled_by": cancelled_by,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "message_type": "cancellation_request"
        }
        
        logger.info(
            f"Publishing cancellation request for run '{run_id}'",
            extra={
                "run_id": run_id,
                "cancelled_by": cancelled_by,
                "topic": settings.kafka_cancellation_topic
            }
        )
        
        try:
            await producer.publish(
                topic=settings.kafka_cancellation_topic,
                message=message,
                key=run_id
            )
            
            logger.info(
                f"Successfully published cancellation request for run '{run_id}'",
                extra={
                    "run_id": run_id,
                    "cancelled_by": cancelled_by
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to publish cancellation request for run '{run_id}': {e}",
                extra={
                    "run_id": run_id,
                    "cancelled_by": cancelled_by,
                    "error": str(e)
                }
            )
            raise
    
    def close(self) -> None:
        """
        Close the Kafka producer connection.
        
        This method should be called when the service is no longer needed
        to properly clean up resources. If an external producer client was
        provided during initialization, it will not be closed.
        """
        if self._producer_client and not self._is_external_client:
            try:
                self._producer_client.close()
                logger.info("Kafka producer connection closed")
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")
            finally:
                self._producer_client = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
