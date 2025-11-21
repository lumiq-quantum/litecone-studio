"""Circuit Breaker implementation for agent resilience."""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"          # Normal operation, all calls go through
    OPEN = "open"              # Failing, reject all calls immediately
    HALF_OPEN = "half_open"    # Testing recovery, allow limited calls


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    enabled: bool = True
    failure_threshold: int = 5
    failure_rate_threshold: float = 0.5
    timeout_seconds: int = 60
    half_open_max_calls: int = 3
    window_size_seconds: int = 120


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreakerStateStore:
    """
    Shared state storage for circuit breakers using Redis.
    
    Enables circuit breaker state to be shared across multiple
    executor instances.
    """
    
    def __init__(self, redis_client: redis.Redis):
        """
        Initialize state store.
        
        Args:
            redis_client: Async Redis client instance
        """
        self.redis = redis_client
    
    async def get_state(self, agent_name: str) -> CircuitState:
        """
        Get current circuit state for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Current circuit state (defaults to CLOSED if not set)
        """
        key = f"circuit_breaker:{agent_name}:state"
        state_str = await self.redis.get(key)
        
        if not state_str:
            return CircuitState.CLOSED
        
        return CircuitState(state_str.decode())
    
    async def set_state(self, agent_name: str, state: CircuitState) -> None:
        """
        Set circuit state for an agent.
        
        Args:
            agent_name: Name of the agent
            state: New circuit state
        """
        key = f"circuit_breaker:{agent_name}:state"
        await self.redis.set(key, state.value)
        
        logger.info(
            f"Circuit breaker state changed to {state.value} for agent '{agent_name}'",
            extra={'agent_name': agent_name, 'state': state.value}
        )
    
    async def record_call(self, agent_name: str, success: bool) -> None:
        """
        Record a call result in sliding window.
        
        Args:
            agent_name: Name of the agent
            success: Whether the call succeeded
        """
        key = f"circuit_breaker:{agent_name}:calls"
        timestamp = datetime.utcnow().timestamp()
        value = f"{timestamp}:{1 if success else 0}"
        
        # Add to sorted set with timestamp as score
        await self.redis.zadd(key, {value: timestamp})
        
        # Remove old entries (outside window)
        window_start = timestamp - 120  # 2 minutes default
        await self.redis.zremrangebyscore(key, 0, window_start)
    
    async def get_recent_calls(
        self,
        agent_name: str,
        window_seconds: int
    ) -> List[bool]:
        """
        Get recent call results within window.
        
        Args:
            agent_name: Name of the agent
            window_seconds: Size of sliding window in seconds
            
        Returns:
            List of boolean values (True=success, False=failure)
        """
        key = f"circuit_breaker:{agent_name}:calls"
        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds
        
        # Get calls within window
        calls = await self.redis.zrangebyscore(
            key,
            window_start,
            now
        )
        
        # Parse results
        return [
            bool(int(call.decode().split(':')[1]))
            for call in calls
        ]
    
    async def get_open_timestamp(self, agent_name: str) -> Optional[datetime]:
        """
        Get timestamp when circuit was opened.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Timestamp when circuit was opened, or None if not set
        """
        key = f"circuit_breaker:{agent_name}:open_timestamp"
        timestamp_str = await self.redis.get(key)
        
        if not timestamp_str:
            return None
        
        return datetime.fromisoformat(timestamp_str.decode())
    
    async def set_open_timestamp(self, agent_name: str, timestamp: datetime) -> None:
        """
        Set timestamp when circuit was opened.
        
        Args:
            agent_name: Name of the agent
            timestamp: Timestamp when circuit was opened
        """
        key = f"circuit_breaker:{agent_name}:open_timestamp"
        await self.redis.set(key, timestamp.isoformat())
    
    async def increment_success(self, agent_name: str) -> int:
        """
        Increment success counter for half-open state.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            New success count
        """
        key = f"circuit_breaker:{agent_name}:half_open_success"
        return await self.redis.incr(key)
    
    async def get_half_open_calls(self, agent_name: str) -> int:
        """
        Get number of calls made in half-open state.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Number of calls in half-open state
        """
        key = f"circuit_breaker:{agent_name}:half_open_calls"
        count = await self.redis.get(key)
        return int(count) if count else 0
    
    async def increment_half_open_calls(self, agent_name: str) -> int:
        """
        Increment half-open calls counter.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            New call count
        """
        key = f"circuit_breaker:{agent_name}:half_open_calls"
        return await self.redis.incr(key)
    
    async def reset_counters(self, agent_name: str) -> None:
        """
        Reset all counters for an agent.
        
        Args:
            agent_name: Name of the agent
        """
        keys = [
            f"circuit_breaker:{agent_name}:half_open_success",
            f"circuit_breaker:{agent_name}:half_open_calls"
        ]
        for key in keys:
            await self.redis.delete(key)


class CircuitBreaker:
    """
    Circuit breaker for a single agent.
    
    States:
    - CLOSED: Normal operation, all calls go through
    - OPEN: Agent is failing, reject all calls immediately
    - HALF_OPEN: Testing recovery, allow limited calls
    """
    
    def __init__(
        self,
        agent_name: str,
        config: CircuitBreakerConfig,
        state_store: CircuitBreakerStateStore
    ):
        """
        Initialize circuit breaker.
        
        Args:
            agent_name: Name of the agent
            config: Circuit breaker configuration
            state_store: Shared state store
        """
        self.agent_name = agent_name
        self.config = config
        self.state_store = state_store
    
    async def call(self, operation: Callable) -> Any:
        """
        Execute operation through circuit breaker.
        
        Args:
            operation: Async callable to execute
            
        Returns:
            Result of the operation
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if not self.config.enabled:
            return await operation()
        
        # Check circuit state
        state = await self.state_store.get_state(self.agent_name)
        
        if state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if await self._should_attempt_reset():
                await self.state_store.set_state(
                    self.agent_name,
                    CircuitState.HALF_OPEN
                )
                await self.state_store.reset_counters(self.agent_name)
                state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN for agent '{self.agent_name}'"
                )
        
        if state == CircuitState.HALF_OPEN:
            # Check if we can make a test call
            if not await self._can_make_half_open_call():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is HALF_OPEN, max calls reached for agent '{self.agent_name}'"
                )
            
            # Increment half-open call counter
            await self.state_store.increment_half_open_calls(self.agent_name)
        
        # Execute operation
        try:
            result = await operation()
            await self._record_success()
            return result
        
        except Exception as e:
            await self._record_failure()
            raise
    
    async def _record_success(self) -> None:
        """Record successful call."""
        state = await self.state_store.get_state(self.agent_name)
        
        if state == CircuitState.HALF_OPEN:
            # Transition to CLOSED if enough successes
            success_count = await self.state_store.increment_success(
                self.agent_name
            )
            if success_count >= self.config.half_open_max_calls:
                await self.state_store.set_state(
                    self.agent_name,
                    CircuitState.CLOSED
                )
                await self.state_store.reset_counters(self.agent_name)
                
                logger.info(
                    f"Circuit breaker transitioned to CLOSED for agent '{self.agent_name}' "
                    f"after {success_count} successful test calls",
                    extra={'agent_name': self.agent_name, 'success_count': success_count}
                )
        
        elif state == CircuitState.CLOSED:
            # Just record the success
            await self.state_store.record_call(
                self.agent_name,
                success=True
            )
    
    async def _record_failure(self) -> None:
        """Record failed call."""
        state = await self.state_store.get_state(self.agent_name)
        
        if state == CircuitState.HALF_OPEN:
            # Transition back to OPEN
            await self.state_store.set_state(
                self.agent_name,
                CircuitState.OPEN
            )
            await self.state_store.set_open_timestamp(
                self.agent_name,
                datetime.utcnow()
            )
            
            logger.warning(
                f"Circuit breaker transitioned back to OPEN for agent '{self.agent_name}' "
                f"due to failure in half-open state",
                extra={'agent_name': self.agent_name}
            )
        
        elif state == CircuitState.CLOSED:
            # Record failure and check thresholds
            await self.state_store.record_call(
                self.agent_name,
                success=False
            )
            
            # Check if we should open the circuit
            if await self._should_open_circuit():
                await self.state_store.set_state(
                    self.agent_name,
                    CircuitState.OPEN
                )
                await self.state_store.set_open_timestamp(
                    self.agent_name,
                    datetime.utcnow()
                )
                
                logger.warning(
                    f"Circuit breaker OPENED for agent '{self.agent_name}' due to failures",
                    extra={'agent_name': self.agent_name}
                )
    
    async def _should_open_circuit(self) -> bool:
        """
        Check if circuit should be opened.
        
        Returns:
            True if circuit should be opened
        """
        # Get recent call history
        calls = await self.state_store.get_recent_calls(
            self.agent_name,
            window_seconds=self.config.window_size_seconds
        )
        
        if len(calls) < self.config.failure_threshold:
            return False
        
        # Check consecutive failures
        recent_failures = sum(1 for c in calls[-self.config.failure_threshold:] if not c)
        if recent_failures >= self.config.failure_threshold:
            logger.info(
                f"Circuit breaker threshold reached: {recent_failures} consecutive failures",
                extra={'agent_name': self.agent_name, 'failures': recent_failures}
            )
            return True
        
        # Check failure rate
        total_calls = len(calls)
        failed_calls = sum(1 for c in calls if not c)
        failure_rate = failed_calls / total_calls
        
        if failure_rate >= self.config.failure_rate_threshold:
            logger.info(
                f"Circuit breaker failure rate threshold reached: {failure_rate:.2%}",
                extra={
                    'agent_name': self.agent_name,
                    'failure_rate': failure_rate,
                    'failed_calls': failed_calls,
                    'total_calls': total_calls
                }
            )
            return True
        
        return False
    
    async def _should_attempt_reset(self) -> bool:
        """
        Check if enough time has passed to attempt reset.
        
        Returns:
            True if circuit should attempt reset
        """
        open_timestamp = await self.state_store.get_open_timestamp(
            self.agent_name
        )
        
        if not open_timestamp:
            return True
        
        elapsed = (datetime.utcnow() - open_timestamp).total_seconds()
        should_reset = elapsed >= self.config.timeout_seconds
        
        if should_reset:
            logger.info(
                f"Circuit breaker timeout elapsed ({elapsed:.1f}s), attempting reset",
                extra={'agent_name': self.agent_name, 'elapsed_seconds': elapsed}
            )
        
        return should_reset
    
    async def _can_make_half_open_call(self) -> bool:
        """
        Check if we can make a call in half-open state.
        
        Returns:
            True if call is allowed
        """
        half_open_calls = await self.state_store.get_half_open_calls(
            self.agent_name
        )
        return half_open_calls < self.config.half_open_max_calls


class CircuitBreakerManager:
    """
    Manages circuit breakers for all agents.
    
    Provides a centralized interface for circuit breaker operations.
    """
    
    def __init__(self, redis_url: str, default_config: CircuitBreakerConfig):
        """
        Initialize circuit breaker manager.
        
        Args:
            redis_url: Redis connection URL
            default_config: Default circuit breaker configuration
        """
        self.redis_url = redis_url
        self.default_config = default_config
        self.redis_client: Optional[redis.Redis] = None
        self.state_store: Optional[CircuitBreakerStateStore] = None
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        logger.info(
            "Initialized CircuitBreakerManager",
            extra={'redis_url': redis_url, 'default_config': default_config}
        )
    
    async def initialize(self) -> None:
        """Initialize Redis connection and state store."""
        self.redis_client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=False
        )
        self.state_store = CircuitBreakerStateStore(self.redis_client)
        
        logger.info("CircuitBreakerManager initialized with Redis connection")
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("CircuitBreakerManager Redis connection closed")
    
    def get_circuit_breaker(
        self,
        agent_name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """
        Get or create circuit breaker for agent.
        
        Args:
            agent_name: Name of the agent
            config: Optional agent-specific configuration
            
        Returns:
            Circuit breaker instance
        """
        if agent_name not in self.circuit_breakers:
            if not self.state_store:
                raise RuntimeError("CircuitBreakerManager not initialized")
            
            # Use agent-specific config or default
            breaker_config = config or self.default_config
            
            self.circuit_breakers[agent_name] = CircuitBreaker(
                agent_name=agent_name,
                config=breaker_config,
                state_store=self.state_store
            )
            
            logger.debug(
                f"Created circuit breaker for agent '{agent_name}'",
                extra={'agent_name': agent_name, 'config': breaker_config}
            )
        
        return self.circuit_breakers[agent_name]
