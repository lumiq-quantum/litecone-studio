#!/usr/bin/env python3
"""
Example script demonstrating configuration usage.

This script shows how to load and use configuration in both
the Centralized Executor and External Agent Executor (Bridge).
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config, load_config


def example_basic_usage():
    """Example: Basic configuration loading."""
    print("=" * 60)
    print("Example 1: Basic Configuration Loading")
    print("=" * 60)
    
    # Set required environment variables
    os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost:5432/workflow_db'
    os.environ['AGENT_REGISTRY_URL'] = 'http://localhost:8080'
    
    # Load configuration
    config = Config()
    
    print(f"✓ Configuration loaded successfully")
    print(f"\nKafka Configuration:")
    print(f"  Brokers: {config.kafka.brokers}")
    print(f"  Client ID: {config.kafka.client_id}")
    print(f"  Tasks Topic: {config.kafka.tasks_topic}")
    print(f"  Results Topic: {config.kafka.results_topic}")
    
    print(f"\nDatabase Configuration:")
    print(f"  URL: {config.database.url}")
    print(f"  Pool Size: {config.database.pool_size}")
    print(f"  Max Overflow: {config.database.max_overflow}")
    
    print(f"\nAgent Registry Configuration:")
    print(f"  URL: {config.agent_registry.url}")
    print(f"  Cache TTL: {config.agent_registry.cache_ttl_seconds}s")
    
    print(f"\nBridge Configuration:")
    print(f"  HTTP Timeout: {config.get_http_timeout_seconds()}s")
    print(f"  Max Retries: {config.bridge.max_retries}")
    print(f"  Backoff Multiplier: {config.bridge.backoff_multiplier}")
    
    print(f"\nLogging Configuration:")
    print(f"  Level: {config.logging.level}")
    print(f"  Format: {config.logging.format}")
    print()


def example_custom_values():
    """Example: Loading configuration with custom values."""
    print("=" * 60)
    print("Example 2: Custom Configuration Values")
    print("=" * 60)
    
    # Set custom environment variables
    os.environ['DATABASE_URL'] = 'postgresql://custom:pass@db.example.com:5432/mydb'
    os.environ['AGENT_REGISTRY_URL'] = 'https://registry.example.com'
    os.environ['KAFKA_BROKERS'] = 'kafka1:9092,kafka2:9092,kafka3:9092'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    os.environ['HTTP_TIMEOUT_MS'] = '60000'
    os.environ['MAX_RETRIES'] = '5'
    
    # Load configuration
    config = Config()
    
    print(f"✓ Configuration loaded with custom values")
    print(f"\nKafka Brokers: {config.kafka.brokers}")
    print(f"Database URL: {config.database.url}")
    print(f"Agent Registry URL: {config.agent_registry.url}")
    print(f"Log Level: {config.logging.level}")
    print(f"HTTP Timeout: {config.get_http_timeout_seconds()}s")
    print(f"Max Retries: {config.bridge.max_retries}")
    print()


def example_executor_config():
    """Example: Executor-specific configuration."""
    print("=" * 60)
    print("Example 3: Executor Configuration")
    print("=" * 60)
    
    # Set executor-specific environment variables
    os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost:5432/workflow_db'
    os.environ['AGENT_REGISTRY_URL'] = 'http://localhost:8080'
    os.environ['RUN_ID'] = 'run-12345'
    os.environ['WORKFLOW_PLAN'] = '/path/to/workflow.json'
    os.environ['WORKFLOW_INPUT'] = '{"topic": "AI", "style": "technical"}'
    
    # Load configuration
    config = Config()
    
    print(f"✓ Executor configuration loaded")
    print(f"\nExecutor Settings:")
    print(f"  Run ID: {config.executor.run_id}")
    print(f"  Workflow Plan: {config.executor.workflow_plan}")
    print(f"  Workflow Input: {config.executor.workflow_input}")
    
    # Validate executor config
    try:
        config.validate_executor_config()
        print(f"\n✓ Executor configuration is valid")
    except ValueError as e:
        print(f"\n✗ Executor configuration is invalid: {e}")
    print()


def example_validation_errors():
    """Example: Configuration validation errors."""
    print("=" * 60)
    print("Example 4: Configuration Validation")
    print("=" * 60)
    
    # Test 1: Missing required field
    print("\nTest 1: Missing DATABASE_URL")
    os.environ.pop('DATABASE_URL', None)
    os.environ['AGENT_REGISTRY_URL'] = 'http://localhost:8080'
    try:
        config = Config()
        print("✗ Should have failed")
    except Exception as e:
        print(f"✓ Validation error caught: {type(e).__name__}")
    
    # Test 2: Invalid database URL
    print("\nTest 2: Invalid DATABASE_URL format")
    os.environ['DATABASE_URL'] = 'mysql://invalid'
    try:
        config = Config()
        print("✗ Should have failed")
    except ValueError as e:
        print(f"✓ Validation error caught: Database URL must be PostgreSQL")
    
    # Test 3: Invalid agent registry URL
    print("\nTest 3: Invalid AGENT_REGISTRY_URL format")
    os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost:5432/db'
    os.environ['AGENT_REGISTRY_URL'] = 'not-a-url'
    try:
        config = Config()
        print("✗ Should have failed")
    except ValueError as e:
        print(f"✓ Validation error caught: URL must start with http:// or https://")
    
    # Test 4: Invalid log level
    print("\nTest 4: Invalid LOG_LEVEL")
    os.environ['AGENT_REGISTRY_URL'] = 'http://localhost:8080'
    os.environ['LOG_LEVEL'] = 'INVALID'
    try:
        config = Config()
        print("✗ Should have failed")
    except ValueError as e:
        print(f"✓ Validation error caught: Invalid log level")
    
    print()


def example_env_file():
    """Example: Loading from .env file."""
    print("=" * 60)
    print("Example 5: Loading from .env File")
    print("=" * 60)
    
    # Clear any invalid environment variables from previous tests
    os.environ.pop('LOG_LEVEL', None)
    
    # Create a temporary .env file
    env_content = """
DATABASE_URL=postgresql://envfile:pass@localhost:5432/envdb
AGENT_REGISTRY_URL=http://registry.local:8080
KAFKA_BROKERS=kafka.local:9092
LOG_LEVEL=WARNING
HTTP_TIMEOUT_MS=45000
"""
    
    with open('.env.example.tmp', 'w') as f:
        f.write(env_content)
    
    try:
        # Load from .env file
        config = load_config(env_file='.env.example.tmp')
        
        print(f"✓ Configuration loaded from .env file")
        print(f"\nValues from .env file:")
        print(f"  Database URL: {config.database.url}")
        print(f"  Agent Registry URL: {config.agent_registry.url}")
        print(f"  Kafka Brokers: {config.kafka.brokers}")
        print(f"  Log Level: {config.logging.level}")
        print(f"  HTTP Timeout: {config.get_http_timeout_seconds()}s")
    finally:
        # Clean up
        if os.path.exists('.env.example.tmp'):
            os.remove('.env.example.tmp')
    
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Configuration Management Examples")
    print("=" * 60 + "\n")
    
    try:
        example_basic_usage()
        example_custom_values()
        example_executor_config()
        example_validation_errors()
        example_env_file()
        
        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
