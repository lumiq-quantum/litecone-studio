# Agent Registry Client

HTTP client for interacting with the Agent Registry service with built-in retry logic and caching.

## Features

- **Async HTTP client** using httpx
- **Exponential backoff retry logic** for transient failures
- **In-memory caching** with configurable TTL
- **Automatic cache invalidation** on expiry

## Usage

### Basic Usage

```python
from agent_registry import AgentRegistryClient

# Initialize the client
client = AgentRegistryClient(
    registry_url="http://agent-registry:8080",
    cache_ttl_seconds=300  # Cache for 5 minutes
)

# Fetch agent metadata (with caching)
metadata = await client.get_agent("ResearchAgent")

print(f"Agent URL: {metadata.url}")
print(f"Timeout: {metadata.timeout}ms")

# Close the client when done
await client.close()
```

### Using as Context Manager

```python
async with AgentRegistryClient("http://agent-registry:8080") as client:
    metadata = await client.get_agent("WriterAgent")
    # Client automatically closes on exit
```

### Custom Retry Configuration

```python
from agent_registry import AgentRegistryClient, RetryConfig

retry_config = RetryConfig(
    max_retries=5,
    initial_delay_ms=500,
    max_delay_ms=10000,
    backoff_multiplier=2.0
)

client = AgentRegistryClient(
    registry_url="http://agent-registry:8080",
    retry_config=retry_config
)
```

### Cache Management

```python
# Clear cache for specific agent
client.clear_cache("ResearchAgent")

# Clear entire cache
client.clear_cache()
```

## Models

### AgentMetadata

```python
class AgentMetadata:
    name: str                           # Agent name
    url: str                            # HTTP endpoint URL
    auth_config: Optional[Dict[str, str]]  # Authentication config
    timeout: int                        # Request timeout in ms
    retry_config: RetryConfig           # Retry configuration
```

### RetryConfig

```python
class RetryConfig:
    max_retries: int = 3               # Maximum retry attempts
    initial_delay_ms: int = 1000       # Initial delay
    max_delay_ms: int = 30000          # Maximum delay
    backoff_multiplier: float = 2.0    # Backoff multiplier
```

## Error Handling

The client automatically retries on:
- Network errors (connection failures, timeouts)
- 5xx server errors
- 429 Too Many Requests

Non-retriable errors:
- 404 Not Found (raises `ValueError`)
- Other 4xx client errors
- Invalid response format

```python
try:
    metadata = await client.get_agent("NonExistentAgent")
except ValueError as e:
    print(f"Agent not found: {e}")
except httpx.HTTPError as e:
    print(f"HTTP error: {e}")
```
