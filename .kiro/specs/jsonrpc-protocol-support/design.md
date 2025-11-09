# Design Document: JSON-RPC 2.0 Protocol Support

## Overview

This design adds dual protocol support to the workflow orchestration system, enabling it to work with both Simple A2A and JSON-RPC 2.0 agents. The design uses an adapter pattern to translate between protocols transparently.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Workflow Executor                        │
│                  (Protocol Agnostic)                         │
└────────────────────────┬────────────────────────────────────┘
                         │ Kafka (AgentTask)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   HTTP-Kafka Bridge                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Protocol Adapter Factory                    │  │
│  │  ┌─────────────────┐    ┌──────────────────────┐    │  │
│  │  │ SimpleA2AAdapter│    │  JsonRpc2Adapter     │    │  │
│  │  └─────────────────┘    └──────────────────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Agents                           │
│  ┌──────────────────┐         ┌──────────────────────┐     │
│  │  Simple A2A      │         │   JSON-RPC 2.0       │     │
│  │  Agent           │         │   Agent              │     │
│  └──────────────────┘         └──────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Registry                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Agent Metadata                                        │  │
│  │  - name: string                                       │  │
│  │  - url: string                                        │  │
│  │  - protocol: "simple-a2a" | "jsonrpc-2.0"           │  │
│  │  - protocol_config: {                                │  │
│  │      method?: string,                                │  │
│  │      version?: string                                │  │
│  │    }                                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Protocol Adapter Interface

**File:** `src/bridge/adapters/protocol_adapter.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from src.models.kafka_messages import AgentTask

class ProtocolAdapter(ABC):
    """Base interface for protocol adapters."""
    
    @abstractmethod
    def to_agent_request(self, task: AgentTask) -> Dict[str, Any]:
        """
        Convert internal task format to agent-specific request format.
        
        Args:
            task: Internal task representation
            
        Returns:
            Request payload in agent's expected format
        """
        pass
    
    @abstractmethod
    def from_agent_response(
        self, 
        response: Dict[str, Any], 
        task_id: str
    ) -> Dict[str, Any]:
        """
        Convert agent response to internal format.
        
        Args:
            response: Agent's response payload
            task_id: Original task ID for correlation
            
        Returns:
            Response in internal format with task_id, status, output, error
        """
        pass
    
    @abstractmethod
    def get_protocol_name(self) -> str:
        """Return the protocol name for logging/debugging."""
        pass
```

### 2. Simple A2A Adapter

**File:** `src/bridge/adapters/simple_a2a_adapter.py`

```python
class SimpleA2AAdapter(ProtocolAdapter):
    """Adapter for Simple A2A HTTP protocol (current format)."""
    
    def to_agent_request(self, task: AgentTask) -> Dict[str, Any]:
        """
        Convert to Simple A2A format:
        {
            "task_id": "...",
            "input": {...}
        }
        """
        return {
            'task_id': task.task_id,
            'input': task.input_data
        }
    
    def from_agent_response(
        self, 
        response: Dict[str, Any], 
        task_id: str
    ) -> Dict[str, Any]:
        """
        Validate and return Simple A2A response:
        {
            "task_id": "...",
            "status": "success" | "error",
            "output": {...},
            "error": null | "..."
        }
        """
        # Validate response structure
        if 'status' not in response:
            raise ValueError("Response missing 'status' field")
        
        # Ensure task_id matches
        if response.get('task_id') != task_id:
            logger.warning(
                f"Response task_id mismatch: expected {task_id}, "
                f"got {response.get('task_id')}"
            )
            response['task_id'] = task_id
        
        return response
    
    def get_protocol_name(self) -> str:
        return "simple-a2a"
```

### 3. JSON-RPC 2.0 Adapter

**File:** `src/bridge/adapters/jsonrpc_adapter.py`

```python
class JsonRpc2Adapter(ProtocolAdapter):
    """Adapter for JSON-RPC 2.0 A2A protocol."""
    
    def __init__(self, method: str = "message/send", version: str = "2.0"):
        self.method = method
        self.version = version
    
    def to_agent_request(self, task: AgentTask) -> Dict[str, Any]:
        """
        Convert to JSON-RPC 2.0 format:
        {
            "jsonrpc": "2.0",
            "id": "...",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "messageId": "...",
                    "parts": [...]
                }
            }
        }
        """
        return {
            'jsonrpc': self.version,
            'id': task.task_id,
            'method': self.method,
            'params': {
                'message': {
                    'role': 'user',
                    'messageId': f"msg-{task.task_id}",
                    'parts': self._convert_input_to_parts(task.input_data)
                }
            }
        }
    
    def from_agent_response(
        self, 
        response: Dict[str, Any], 
        task_id: str
    ) -> Dict[str, Any]:
        """
        Convert JSON-RPC 2.0 response to internal format.
        
        JSON-RPC Success:
        {
            "jsonrpc": "2.0",
            "id": "...",
            "result": {
                "status": {"state": "completed"},
                "artifacts": [...],
                ...
            }
        }
        
        JSON-RPC Error:
        {
            "jsonrpc": "2.0",
            "id": "...",
            "error": {
                "code": -32600,
                "message": "Invalid Request"
            }
        }
        """
        # Validate JSON-RPC structure
        if 'jsonrpc' not in response:
            raise ValueError("Response missing 'jsonrpc' field")
        
        if response['jsonrpc'] != self.version:
            raise ValueError(
                f"Unsupported JSON-RPC version: {response['jsonrpc']}"
            )
        
        # Check for error response
        if 'error' in response:
            error_obj = response['error']
            return {
                'task_id': task_id,
                'status': 'error',
                'output': None,
                'error': f"JSON-RPC Error {error_obj.get('code')}: "
                         f"{error_obj.get('message')}"
            }
        
        # Process success response
        if 'result' not in response:
            raise ValueError("Response missing both 'result' and 'error'")
        
        result = response['result']
        
        # Extract status
        status_obj = result.get('status', {})
        state = status_obj.get('state', 'unknown')
        status = 'success' if state == 'completed' else 'error'
        
        # Extract output from artifacts or result
        output = self._extract_output(result)
        
        return {
            'task_id': task_id,
            'status': status,
            'output': output,
            'error': None if status == 'success' else f"Task state: {state}"
        }
    
    def _convert_input_to_parts(self, input_data: Dict[str, Any]) -> list:
        """Convert input data to message parts."""
        parts = []
        
        # If input has a 'text' or 'query' field, use it directly
        if isinstance(input_data, dict):
            text_content = input_data.get('text') or input_data.get('query')
            if text_content:
                parts.append({
                    'kind': 'text',
                    'text': str(text_content)
                })
            else:
                # Convert entire input to JSON string
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
    
    def _extract_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract output from JSON-RPC result."""
        output = {}
        
        # Extract from artifacts
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
                output['artifacts'] = artifacts
        
        # Extract from history (last agent message)
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
        
        # Include metadata if present
        if 'metadata' in result:
            output['metadata'] = result['metadata']
        
        # Include context ID for potential future use
        if 'contextId' in result:
            output['context_id'] = result['contextId']
        
        # If no output extracted, return full result
        if not output:
            output = result
        
        return output
    
    def get_protocol_name(self) -> str:
        return "jsonrpc-2.0"
```

### 4. Protocol Adapter Factory

**File:** `src/bridge/adapters/adapter_factory.py`

```python
class ProtocolAdapterFactory:
    """Factory for creating protocol adapters based on agent configuration."""
    
    _adapters = {
        'simple-a2a': SimpleA2AAdapter,
        'jsonrpc-2.0': JsonRpc2Adapter
    }
    
    @classmethod
    def create_adapter(
        cls, 
        protocol: str, 
        protocol_config: Optional[Dict[str, Any]] = None
    ) -> ProtocolAdapter:
        """
        Create appropriate protocol adapter.
        
        Args:
            protocol: Protocol name ("simple-a2a" or "jsonrpc-2.0")
            protocol_config: Optional protocol-specific configuration
            
        Returns:
            Protocol adapter instance
            
        Raises:
            ValueError: If protocol is not supported
        """
        if protocol not in cls._adapters:
            supported = ', '.join(cls._adapters.keys())
            raise ValueError(
                f"Unsupported protocol: {protocol}. "
                f"Supported protocols: {supported}"
            )
        
        adapter_class = cls._adapters[protocol]
        
        # Pass config to adapter if it accepts it
        if protocol_config and protocol == 'jsonrpc-2.0':
            return adapter_class(
                method=protocol_config.get('method', 'message/send'),
                version=protocol_config.get('version', '2.0')
            )
        
        return adapter_class()
    
    @classmethod
    def register_adapter(cls, protocol: str, adapter_class: type):
        """Register a new protocol adapter (for extensibility)."""
        cls._adapters[protocol] = adapter_class
    
    @classmethod
    def supported_protocols(cls) -> list:
        """Return list of supported protocol names."""
        return list(cls._adapters.keys())
```

## Data Models

### Agent Metadata Extension

**File:** `src/database/models.py`

```python
class Agent(Base):
    __tablename__ = 'agents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False, index=True)
    url = Column(String, nullable=False)
    description = Column(String)
    
    # Protocol configuration
    protocol = Column(
        String, 
        nullable=False, 
        default='simple-a2a',
        comment='Protocol type: simple-a2a or jsonrpc-2.0'
    )
    protocol_config = Column(
        JSONB,
        comment='Protocol-specific configuration'
    )
    
    # ... rest of fields
```

### API Schema Extension

**File:** `api/schemas/agent.py`

```python
class AgentProtocol(str, Enum):
    """Supported agent protocols."""
    SIMPLE_A2A = "simple-a2a"
    JSONRPC_2_0 = "jsonrpc-2.0"

class JsonRpcProtocolConfig(BaseModel):
    """Configuration for JSON-RPC 2.0 protocol."""
    method: str = Field(default="message/send", description="JSON-RPC method name")
    version: str = Field(default="2.0", description="JSON-RPC version")

class AgentCreate(BaseModel):
    """Schema for creating an agent."""
    name: str = Field(..., min_length=1, max_length=255)
    url: HttpUrl
    description: Optional[str] = None
    protocol: AgentProtocol = Field(default=AgentProtocol.SIMPLE_A2A)
    protocol_config: Optional[Dict[str, Any]] = None
    # ... rest of fields
    
    @validator('protocol_config')
    def validate_protocol_config(cls, v, values):
        """Validate protocol_config based on protocol type."""
        protocol = values.get('protocol')
        
        if protocol == AgentProtocol.JSONRPC_2_0 and v:
            # Validate JSON-RPC config
            JsonRpcProtocolConfig(**v)
        
        return v
```

## Database Migration

**File:** `alembic/versions/xxx_add_protocol_support.py`

```python
def upgrade():
    # Add protocol column with default
    op.add_column(
        'agents',
        sa.Column(
            'protocol',
            sa.String(),
            nullable=False,
            server_default='simple-a2a',
            comment='Protocol type: simple-a2a or jsonrpc-2.0'
        )
    )
    
    # Add protocol_config JSONB column
    op.add_column(
        'agents',
        sa.Column(
            'protocol_config',
            postgresql.JSONB(),
            nullable=True,
            comment='Protocol-specific configuration'
        )
    )
    
    # Create index on protocol for filtering
    op.create_index(
        'ix_agents_protocol',
        'agents',
        ['protocol']
    )

def downgrade():
    op.drop_index('ix_agents_protocol', table_name='agents')
    op.drop_column('agents', 'protocol_config')
    op.drop_column('agents', 'protocol')
```

## Bridge Integration

### Updated invoke_agent Method

**File:** `src/bridge/external_agent_executor.py`

```python
async def invoke_agent(
    self,
    agent_metadata: AgentMetadata,
    task: AgentTask
) -> Dict[str, Any]:
    """Invoke agent using appropriate protocol adapter."""
    
    # Get protocol adapter
    try:
        adapter = ProtocolAdapterFactory.create_adapter(
            protocol=agent_metadata.protocol,
            protocol_config=agent_metadata.protocol_config
        )
    except ValueError as e:
        logger.error(f"Failed to create protocol adapter: {e}")
        raise
    
    log_event(
        logger, 'info', 'http_call',
        f"Invoking agent '{agent_metadata.name}' using {adapter.get_protocol_name()}",
        agent_name=agent_metadata.name,
        protocol=adapter.get_protocol_name(),
        task_id=task.task_id
    )
    
    # Convert task to agent request format
    try:
        request_payload = adapter.to_agent_request(task)
    except Exception as e:
        logger.error(
            f"Failed to convert request to {adapter.get_protocol_name()}: {e}",
            extra={'task_id': task.task_id, 'agent': agent_metadata.name}
        )
        raise
    
    # Prepare headers
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Correlation-ID': task.correlation_id
    }
    
    # Add authentication
    self._add_auth_headers(headers, agent_metadata)
    
    # Make HTTP request
    timeout = agent_metadata.timeout / 1000.0
    
    try:
        response = await self.http_client.post(
            agent_metadata.url,
            json=request_payload,
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()
        response_data = response.json()
    except Exception as e:
        logger.error(f"HTTP request failed: {e}")
        raise
    
    # Convert response to internal format
    try:
        result = adapter.from_agent_response(response_data, task.task_id)
    except Exception as e:
        logger.error(
            f"Failed to convert response from {adapter.get_protocol_name()}: {e}",
            extra={
                'task_id': task.task_id,
                'agent': agent_metadata.name,
                'response': response_data
            }
        )
        raise
    
    return result
```

## Error Handling

### Protocol Translation Errors

```python
class ProtocolTranslationError(Exception):
    """Raised when protocol translation fails."""
    
    def __init__(
        self,
        message: str,
        protocol: str,
        direction: str,  # 'request' or 'response'
        original_data: Any = None
    ):
        self.protocol = protocol
        self.direction = direction
        self.original_data = original_data
        super().__init__(message)
```

## Testing Strategy

### Unit Tests

1. **Adapter Tests** (`tests/unit/bridge/adapters/`)
   - Test request translation for each adapter
   - Test response translation for each adapter
   - Test error cases
   - Test edge cases (empty input, malformed responses)

2. **Factory Tests** (`tests/unit/bridge/adapters/test_factory.py`)
   - Test adapter creation for each protocol
   - Test unsupported protocol handling
   - Test protocol config passing

### Integration Tests

1. **Mock Agent Tests** (`tests/integration/test_jsonrpc_agent.py`)
   - Create mock JSON-RPC agent
   - Test end-to-end request/response
   - Test error responses
   - Test timeout handling

2. **Bridge Tests** (`tests/integration/test_bridge_protocols.py`)
   - Test bridge with Simple A2A agent
   - Test bridge with JSON-RPC agent
   - Test protocol switching

### End-to-End Tests

1. **Workflow Tests** (`tests/e2e/test_mixed_protocol_workflow.py`)
   - Workflow with both protocol types
   - Verify correct protocol used per agent
   - Verify results are consistent

## Monitoring and Logging

### Log Events

```python
# Request translation
log_event(
    logger, 'debug', 'protocol_request_translation',
    f"Translating request to {protocol}",
    protocol=protocol,
    task_id=task_id,
    input_size=len(str(input_data))
)

# Response translation
log_event(
    logger, 'debug', 'protocol_response_translation',
    f"Translating response from {protocol}",
    protocol=protocol,
    task_id=task_id,
    response_size=len(str(response_data))
)

# Translation error
log_event(
    logger, 'error', 'protocol_translation_error',
    f"Failed to translate {direction} for {protocol}",
    protocol=protocol,
    direction=direction,
    error=str(error),
    data=data
)
```

### Metrics

```python
# Protocol usage counter
protocol_requests_total = Counter(
    'agent_protocol_requests_total',
    'Total agent requests by protocol',
    ['protocol', 'agent_name']
)

# Translation duration
protocol_translation_duration = Histogram(
    'protocol_translation_duration_seconds',
    'Time spent translating protocols',
    ['protocol', 'direction']
)

# Translation errors
protocol_translation_errors = Counter(
    'protocol_translation_errors_total',
    'Protocol translation errors',
    ['protocol', 'direction', 'error_type']
)
```

## Deployment Considerations

### Rollout Strategy

1. **Phase 1**: Deploy with Simple A2A only (default)
2. **Phase 2**: Add JSON-RPC support, test with one agent
3. **Phase 3**: Gradually migrate agents to JSON-RPC
4. **Phase 4**: Monitor and optimize

### Configuration

```yaml
# Agent configuration example
agents:
  - name: "LegacyAgent"
    url: "http://legacy:8080"
    protocol: "simple-a2a"
  
  - name: "ModernAgent"
    url: "http://modern:8001"
    protocol: "jsonrpc-2.0"
    protocol_config:
      method: "message/send"
      version: "2.0"
```

## Future Enhancements

1. **Additional Protocols**: gRPC, GraphQL
2. **Protocol Negotiation**: Auto-detect protocol
3. **Protocol Versioning**: Support multiple JSON-RPC versions
4. **Streaming Support**: For long-running tasks
5. **Batch Requests**: JSON-RPC batch support
