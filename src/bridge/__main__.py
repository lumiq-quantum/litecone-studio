"""Entry point for the External Agent Executor (HTTP-Kafka Bridge)."""

import asyncio
import logging
import os
import signal
import sys

from src.bridge.external_agent_executor import ExternalAgentExecutor
from src.utils.logging import setup_logging, log_event

logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Main entry point for the External Agent Executor.
    
    Initializes the executor, starts the main loop, and handles graceful shutdown.
    """
    # Configure structured logging
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = os.getenv('LOG_FORMAT', 'json').lower()
    setup_logging(log_level=log_level, log_format=log_format)
    
    # Load configuration from environment variables
    kafka_bootstrap_servers = os.getenv('KAFKA_BROKERS', 'localhost:9092')
    agent_registry_url = os.getenv('AGENT_REGISTRY_URL', 'http://localhost:8080')
    tasks_topic = os.getenv('TASKS_TOPIC', 'orchestrator.tasks.http')
    results_topic = os.getenv('RESULTS_TOPIC', 'results.topic')
    consumer_group_id = os.getenv('CONSUMER_GROUP_ID', 'external-agent-executor-group')
    http_timeout_seconds = int(os.getenv('HTTP_TIMEOUT_SECONDS', '30'))
    max_retries = int(os.getenv('MAX_RETRIES', '3'))
    
    log_event(
        logger, 'info', 'bridge_start',
        "Starting External Agent Executor (HTTP-Kafka Bridge)",
        kafka_brokers=kafka_bootstrap_servers,
        agent_registry_url=agent_registry_url,
        tasks_topic=tasks_topic,
        results_topic=results_topic,
        consumer_group_id=consumer_group_id,
        http_timeout_seconds=http_timeout_seconds,
        max_retries=max_retries,
        log_level=log_level,
        log_format=log_format
    )
    
    # Create executor instance
    executor = ExternalAgentExecutor(
        kafka_bootstrap_servers=kafka_bootstrap_servers,
        agent_registry_url=agent_registry_url,
        tasks_topic=tasks_topic,
        results_topic=results_topic,
        consumer_group_id=consumer_group_id,
        http_timeout_seconds=http_timeout_seconds,
        max_retries=max_retries
    )
    
    # Setup signal handlers for graceful shutdown
    shutdown_event = asyncio.Event()
    
    def signal_handler(sig, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {sig}, initiating graceful shutdown...")
        shutdown_event.set()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize connections
        await executor.initialize()
        
        # Start the executor in a task
        executor_task = asyncio.create_task(executor.start())
        
        # Wait for shutdown signal
        await shutdown_event.wait()
        
        # Stop the executor
        logger.info("Stopping executor...")
        executor.stop()
        
        # Wait for executor task to complete (with timeout)
        try:
            await asyncio.wait_for(executor_task, timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("Executor task did not complete within timeout, cancelling...")
            executor_task.cancel()
            try:
                await executor_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown and cleanup
        await executor.shutdown()
        
        logger.info("External Agent Executor stopped successfully")
        
    except Exception as e:
        logger.error(f"Fatal error in External Agent Executor: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
