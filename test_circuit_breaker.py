"""
Test script for Circuit Breaker functionality.

This script demonstrates circuit breaker behavior by simulating
failing agent calls and verifying state transitions.
"""

import asyncio
import sys
from datetime import datetime

# Mock Redis for testing
class MockRedis:
    """Mock Redis client for testing."""
    
    def __init__(self):
        self.data = {}
        self.sorted_sets = {}
    
    async def get(self, key):
        value = self.data.get(key)
        return value.encode() if value else None
    
    async def set(self, key, value):
        self.data[key] = value
    
    async def zadd(self, key, mapping):
        if key not in self.sorted_sets:
            self.sorted_sets[key] = []
        for value, score in mapping.items():
            self.sorted_sets[key].append((value, score))
    
    async def zrangebyscore(self, key, min_score, max_score):
        if key not in self.sorted_sets:
            return []
        return [
            value.encode() if isinstance(value, str) else value
            for value, score in self.sorted_sets[key]
            if min_score <= score <= max_score
        ]
    
    async def zremrangebyscore(self, key, min_score, max_score):
        if key in self.sorted_sets:
            self.sorted_sets[key] = [
                (value, score)
                for value, score in self.sorted_sets[key]
                if not (min_score <= score <= max_score)
            ]
    
    async def incr(self, key):
        current = int(self.data.get(key, 0))
        self.data[key] = str(current + 1)
        return current + 1
    
    async def delete(self, *keys):
        for key in keys:
            self.data.pop(key, None)
    
    async def close(self):
        pass


async def test_circuit_breaker():
    """Test circuit breaker functionality."""
    
    print("=" * 60)
    print("Circuit Breaker Test")
    print("=" * 60)
    print()
    
    # Import circuit breaker components
    sys.path.insert(0, '.')
    from src.bridge.circuit_breaker import (
        CircuitBreaker,
        CircuitBreakerConfig,
        CircuitBreakerStateStore,
        CircuitState,
        CircuitBreakerOpenError
    )
    
    # Create mock Redis and state store
    redis_client = MockRedis()
    state_store = CircuitBreakerStateStore(redis_client)
    
    # Create circuit breaker with test configuration
    config = CircuitBreakerConfig(
        enabled=True,
        failure_threshold=3,  # Open after 3 failures
        failure_rate_threshold=0.5,
        timeout_seconds=2,  # Short timeout for testing
        half_open_max_calls=2,
        window_size_seconds=60
    )
    
    circuit_breaker = CircuitBreaker(
        agent_name="TestAgent",
        config=config,
        state_store=state_store
    )
    
    # Test 1: Circuit starts CLOSED
    print("Test 1: Initial state should be CLOSED")
    state = await state_store.get_state("TestAgent")
    assert state == CircuitState.CLOSED, f"Expected CLOSED, got {state}"
    print(f"✓ Circuit state: {state.value}")
    print()
    
    # Test 2: Successful calls keep circuit CLOSED
    print("Test 2: Successful calls keep circuit CLOSED")
    for i in range(3):
        async def success_operation():
            return f"Success {i}"
        
        result = await circuit_breaker.call(success_operation)
        print(f"  Call {i+1}: {result}")
    
    state = await state_store.get_state("TestAgent")
    assert state == CircuitState.CLOSED, f"Expected CLOSED, got {state}"
    print(f"✓ Circuit state: {state.value}")
    print()
    
    # Test 3: Consecutive failures open circuit
    print("Test 3: Consecutive failures should open circuit")
    for i in range(3):
        try:
            async def failing_operation():
                raise Exception(f"Failure {i}")
            
            await circuit_breaker.call(failing_operation)
        except Exception as e:
            print(f"  Call {i+1} failed: {e}")
    
    state = await state_store.get_state("TestAgent")
    assert state == CircuitState.OPEN, f"Expected OPEN, got {state}"
    print(f"✓ Circuit state: {state.value}")
    print()
    
    # Test 4: Calls fail immediately when circuit is OPEN
    print("Test 4: Calls should fail immediately when circuit is OPEN")
    try:
        async def any_operation():
            return "Should not execute"
        
        await circuit_breaker.call(any_operation)
        assert False, "Should have raised CircuitBreakerOpenError"
    except CircuitBreakerOpenError as e:
        print(f"  ✓ Call rejected: {e}")
    print()
    
    # Test 5: Circuit transitions to HALF_OPEN after timeout
    print("Test 5: Circuit should transition to HALF_OPEN after timeout")
    print(f"  Waiting {config.timeout_seconds} seconds...")
    await asyncio.sleep(config.timeout_seconds + 0.5)
    
    # First call after timeout should transition to HALF_OPEN
    try:
        async def test_operation():
            return "Test call"
        
        result = await circuit_breaker.call(test_operation)
        print(f"  ✓ Test call succeeded: {result}")
    except CircuitBreakerOpenError:
        print("  ✗ Circuit still open (unexpected)")
    
    state = await state_store.get_state("TestAgent")
    print(f"  Circuit state: {state.value}")
    print()
    
    # Test 6: Successful test calls close circuit
    print("Test 6: Successful test calls should close circuit")
    for i in range(config.half_open_max_calls):
        async def success_operation():
            return f"Test success {i}"
        
        result = await circuit_breaker.call(success_operation)
        print(f"  Test call {i+1}: {result}")
    
    state = await state_store.get_state("TestAgent")
    assert state == CircuitState.CLOSED, f"Expected CLOSED, got {state}"
    print(f"✓ Circuit state: {state.value}")
    print()
    
    # Test 7: Failed test call reopens circuit
    print("Test 7: Failed test call should reopen circuit")
    
    # First, open the circuit again
    for i in range(3):
        try:
            async def failing_operation():
                raise Exception(f"Failure {i}")
            
            await circuit_breaker.call(failing_operation)
        except Exception:
            pass
    
    print("  Circuit opened again")
    
    # Wait for timeout
    await asyncio.sleep(config.timeout_seconds + 0.5)
    
    # Make a failing test call
    try:
        async def failing_test():
            raise Exception("Test failure")
        
        await circuit_breaker.call(failing_test)
    except Exception as e:
        print(f"  Test call failed: {e}")
    
    state = await state_store.get_state("TestAgent")
    assert state == CircuitState.OPEN, f"Expected OPEN, got {state}"
    print(f"✓ Circuit state: {state.value}")
    print()
    
    # Cleanup
    await redis_client.close()
    
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_circuit_breaker())
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
