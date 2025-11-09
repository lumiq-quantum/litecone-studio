"""HTTP client for Agent Registry with retry logic and caching."""

import asyncio
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
import httpx

from .models import AgentMetadata, RetryConfig

logger = logging.getLogger(__name__)


class AgentRegistryClient:
    """Client for interacting with the Agent Registry HTTP API."""
    
    def __init__(
        self,
        registry_url: str,
        cache_ttl_seconds: int = 300,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Initialize the Agent Registry client.
        
        Args:
            registry_url: Base URL of the Agent Registry service
            cache_ttl_seconds: Time-to-live for cached agent metadata in seconds (default: 300)
            retry_config: Retry configuration for HTTP requests (default: RetryConfig())
        """
        self.registry_url = registry_url.rstrip('/')
        self.cache_ttl_seconds = cache_ttl_seconds
        self.retry_config = retry_config or RetryConfig()
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # In-memory cache: agent_name -> (AgentMetadata, expiry_time)
        self._cache: Dict[str, tuple[AgentMetadata, datetime]] = {}
        
        logger.info(
            f"Initialized AgentRegistryClient with registry_url={registry_url}, "
            f"cache_ttl={cache_ttl_seconds}s"
        )
    
    async def get_agent(self, agent_name: str) -> AgentMetadata:
        """
        Retrieve agent metadata from the registry.
        
        First checks the in-memory cache. If not found or expired,
        fetches from the Agent Registry API with retry logic.
        
        Args:
            agent_name: Name of the agent to retrieve
            
        Returns:
            AgentMetadata object containing agent configuration
            
        Raises:
            httpx.HTTPError: If the HTTP request fails after all retries
            ValueError: If the agent is not found or response is invalid
        """
        # Check cache first
        cached_metadata = self._get_from_cache(agent_name)
        if cached_metadata is not None:
            logger.debug(f"Cache hit for agent '{agent_name}'")
            return cached_metadata
        
        logger.debug(f"Cache miss for agent '{agent_name}', fetching from registry")
        
        # Fetch from registry with retry logic
        metadata = await self._fetch_agent_with_retry(agent_name)
        
        # Store in cache
        self._put_in_cache(agent_name, metadata)
        
        return metadata
    
    def _get_from_cache(self, agent_name: str) -> Optional[AgentMetadata]:
        """
        Retrieve agent metadata from cache if present and not expired.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            AgentMetadata if found and valid, None otherwise
        """
        if agent_name not in self._cache:
            return None
        
        metadata, expiry_time = self._cache[agent_name]
        
        # Check if expired
        if datetime.utcnow() >= expiry_time:
            logger.debug(f"Cache entry for agent '{agent_name}' has expired")
            del self._cache[agent_name]
            return None
        
        return metadata
    
    def _put_in_cache(self, agent_name: str, metadata: AgentMetadata) -> None:
        """
        Store agent metadata in cache with TTL.
        
        Args:
            agent_name: Name of the agent
            metadata: AgentMetadata to cache
        """
        expiry_time = datetime.utcnow() + timedelta(seconds=self.cache_ttl_seconds)
        self._cache[agent_name] = (metadata, expiry_time)
        logger.debug(f"Cached metadata for agent '{agent_name}' until {expiry_time.isoformat()}")
    
    def clear_cache(self, agent_name: Optional[str] = None) -> None:
        """
        Clear the cache for a specific agent or all agents.
        
        Args:
            agent_name: Name of the agent to clear, or None to clear all
        """
        if agent_name is None:
            self._cache.clear()
            logger.info("Cleared entire agent metadata cache")
        elif agent_name in self._cache:
            del self._cache[agent_name]
            logger.info(f"Cleared cache for agent '{agent_name}'")
    
    async def _fetch_agent_with_retry(self, agent_name: str) -> AgentMetadata:
        """
        Fetch agent metadata from registry with exponential backoff retry logic.
        
        Args:
            agent_name: Name of the agent to fetch
            
        Returns:
            AgentMetadata object
            
        Raises:
            httpx.HTTPError: If all retry attempts fail
            ValueError: If the agent is not found or response is invalid
        """
        attempt = 0
        delay = self.retry_config.initial_delay_ms / 1000.0  # Convert to seconds
        last_error = None
        
        while attempt < self.retry_config.max_retries:
            try:
                return await self._fetch_agent(agent_name)
            except Exception as error:
                last_error = error
                
                # Check if error is retriable
                if not self._is_retriable_error(error) or attempt == self.retry_config.max_retries - 1:
                    logger.error(
                        f"Failed to fetch agent '{agent_name}' after {attempt + 1} attempts: {error}"
                    )
                    raise error
                
                # Log retry attempt
                logger.warning(
                    f"Attempt {attempt + 1}/{self.retry_config.max_retries} failed for agent "
                    f"'{agent_name}': {error}. Retrying in {delay:.2f}s..."
                )
                
                # Wait before retry
                await asyncio.sleep(delay)
                
                # Calculate next delay with exponential backoff
                delay = min(
                    delay * self.retry_config.backoff_multiplier,
                    self.retry_config.max_delay_ms / 1000.0
                )
                attempt += 1
        
        # Should not reach here, but just in case
        raise last_error or Exception(f"Failed to fetch agent '{agent_name}'")
    
    async def _fetch_agent(self, agent_name: str) -> AgentMetadata:
        """
        Fetch agent metadata from the API database (single attempt).
        Updated to query API database first.
        
        Args:
            agent_name: Name of the agent to fetch
            
        Returns:
            AgentMetadata object
            
        Raises:
            httpx.HTTPError: If the HTTP request fails
            ValueError: If the agent is not found or response is invalid
        """
        # Try API database first (workflow-management-api)
        api_url = f"http://workflow-management-api:8000/api/v1/agents?name={agent_name}"
        
        logger.debug(f"Fetching agent metadata from API database: {api_url}")
        
        try:
            response = await self.http_client.get(api_url)
            
            if response.status_code == 200:
                api_data = response.json()
                if api_data.get('items') and len(api_data['items']) > 0:
                    agent_data = api_data['items'][0]
                    
                    # Convert API format to AgentMetadata format
                    metadata_dict = {
                        "name": agent_data["name"],
                        "url": agent_data["url"],
                        "auth_config": agent_data.get("auth_config"),
                        "timeout": agent_data.get("timeout_ms", 30000),
                        "retry_config": agent_data.get("retry_config", {
                            "max_retries": 3,
                            "initial_delay_ms": 1000,
                            "max_delay_ms": 30000,
                            "backoff_multiplier": 2.0
                        })
                    }
                    
                    metadata = AgentMetadata(**metadata_dict)
                    logger.info(f"Successfully fetched metadata for agent '{agent_name}' from API database")
                    return metadata
        except Exception as e:
            logger.warning(f"Failed to fetch from API database: {e}, falling back to registry")
        
        # Fallback to mock registry for backward compatibility
        url = f"{self.registry_url}/agents/{agent_name}"
        
        logger.debug(f"Fetching agent metadata from registry: {url}")
        
        response = await self.http_client.get(url)
        
        # Handle 404 specifically
        if response.status_code == 404:
            raise ValueError(f"Agent '{agent_name}' not found in API database or registry")
        
        # Raise for other error status codes
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        
        # Validate and create AgentMetadata
        try:
            metadata = AgentMetadata(**data)
            logger.info(f"Successfully fetched metadata for agent '{agent_name}' from registry")
            return metadata
        except Exception as e:
            raise ValueError(f"Invalid agent metadata response for '{agent_name}': {e}")
    
    def _is_retriable_error(self, error: Exception) -> bool:
        """
        Determine if an error is retriable.
        
        Retriable errors include:
        - Network errors (connection failures, timeouts)
        - 5xx server errors
        
        Non-retriable errors include:
        - 4xx client errors (except 429 Too Many Requests)
        - Invalid response format
        
        Args:
            error: The exception to check
            
        Returns:
            True if the error is retriable, False otherwise
        """
        # Network errors are retriable
        if isinstance(error, (httpx.NetworkError, httpx.TimeoutException)):
            return True
        
        # HTTP status errors
        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
            # 5xx errors are retriable
            if 500 <= status_code < 600:
                return True
            # 429 Too Many Requests is retriable
            if status_code == 429:
                return True
            # Other 4xx errors are not retriable
            return False
        
        # Other errors (like ValueError) are not retriable
        return False
    
    async def close(self) -> None:
        """Close the HTTP client and clean up resources."""
        await self.http_client.aclose()
        logger.info("Closed AgentRegistryClient HTTP client")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
