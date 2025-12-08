"""Agent query service for retrieving and matching agents."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import re
from sqlalchemy.ext.asyncio import AsyncSession

from api.repositories.agent import AgentRepository
from api.models.agent import Agent


class AgentMetadata:
    """Metadata for an agent."""
    
    def __init__(
        self,
        name: str,
        description: Optional[str],
        url: str,
        capabilities: List[str],
        status: str
    ):
        self.name = name
        self.description = description
        self.url = url
        self.capabilities = capabilities
        self.status = status
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "capabilities": self.capabilities,
            "status": self.status
        }
    
    @classmethod
    def from_agent(cls, agent: Agent) -> "AgentMetadata":
        """Create AgentMetadata from Agent model."""
        capabilities = cls._extract_capabilities(agent.description or "")
        return cls(
            name=agent.name,
            description=agent.description,
            url=agent.url,
            capabilities=capabilities,
            status=agent.status
        )
    
    @staticmethod
    def _extract_capabilities(description: str) -> List[str]:
        """
        Extract capabilities from agent description.
        
        Looks for common patterns like:
        - "can process data"
        - "handles authentication"
        - "performs validation"
        - Keywords: process, handle, perform, execute, manage, etc.
        
        Args:
            description: Agent description text
            
        Returns:
            List of extracted capability keywords
        """
        if not description:
            return []
        
        # Convert to lowercase for matching
        desc_lower = description.lower()
        
        # Common capability verbs
        capability_verbs = [
            'process', 'handle', 'perform', 'execute', 'manage',
            'validate', 'transform', 'analyze', 'generate', 'create',
            'update', 'delete', 'send', 'receive', 'parse', 'format',
            'authenticate', 'authorize', 'encrypt', 'decrypt', 'store',
            'retrieve', 'query', 'search', 'filter', 'sort', 'aggregate'
        ]
        
        # Extract capabilities based on verb patterns
        capabilities = []
        for verb in capability_verbs:
            # Look for patterns like "can process", "processes", "processing"
            patterns = [
                rf'\b{verb}(?:es|ing|s)?\b',
                rf'\bcan\s+{verb}\b',
                rf'\b{verb}(?:es|ing|s)?\s+\w+\b'
            ]
            for pattern in patterns:
                if re.search(pattern, desc_lower):
                    capabilities.append(verb)
                    break
        
        # Extract domain-specific keywords (nouns)
        domain_keywords = [
            'data', 'file', 'document', 'image', 'video', 'audio',
            'text', 'json', 'xml', 'csv', 'pdf', 'email', 'message',
            'user', 'authentication', 'authorization', 'payment', 'order',
            'workflow', 'task', 'notification', 'report', 'analytics'
        ]
        
        for keyword in domain_keywords:
            if re.search(rf'\b{keyword}(?:s)?\b', desc_lower):
                capabilities.append(keyword)
        
        # Remove duplicates and return
        return list(set(capabilities))


class AgentQueryService:
    """Service for querying and matching agents from the registry."""
    
    # Cache configuration
    CACHE_TTL_SECONDS = 300  # 5 minutes
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the agent query service.
        
        Args:
            db: Database session for querying agents
        """
        self.db = db
        self.repository = AgentRepository(db)
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cache entry is still valid.
        
        Args:
            cache_key: Key to check in cache
            
        Returns:
            True if cache is valid, False otherwise
        """
        if cache_key not in self._cache_timestamps:
            return False
        
        timestamp = self._cache_timestamps[cache_key]
        age = datetime.utcnow() - timestamp
        return age.total_seconds() < self.CACHE_TTL_SECONDS
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        Get value from cache if valid.
        
        Args:
            cache_key: Key to retrieve
            
        Returns:
            Cached value or None if not found or expired
        """
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        return None
    
    def _set_cache(self, cache_key: str, value: Any) -> None:
        """
        Set value in cache with current timestamp.
        
        Args:
            cache_key: Key to store
            value: Value to cache
        """
        self._cache[cache_key] = value
        self._cache_timestamps[cache_key] = datetime.utcnow()
    
    def _clear_cache(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._cache_timestamps.clear()
    
    async def get_all_agents(
        self,
        status: str = "active"
    ) -> List[AgentMetadata]:
        """
        Get all agents from the registry.
        
        Args:
            status: Filter by agent status (default: active)
            
        Returns:
            List of agent metadata
        """
        # Check cache first
        cache_key = f"agents_{status}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # Query database
        agents = await self.repository.list(status=status, limit=1000)
        
        # Convert to metadata
        agent_metadata = [AgentMetadata.from_agent(agent) for agent in agents]
        
        # Cache results
        self._set_cache(cache_key, agent_metadata)
        
        return agent_metadata
    
    async def find_agents_by_capability(
        self,
        capability_description: str
    ) -> List[AgentMetadata]:
        """
        Find agents matching a capability description.
        
        Uses keyword matching to find agents whose capabilities or descriptions
        match the requested capability.
        
        Args:
            capability_description: Description of required capability
            
        Returns:
            List of matching agents, sorted by relevance
        """
        # Get all active agents
        all_agents = await self.get_all_agents(status="active")
        
        if not capability_description:
            return all_agents
        
        # Extract keywords from capability description
        desc_lower = capability_description.lower()
        keywords = set(re.findall(r'\b\w+\b', desc_lower))
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = keywords - stop_words
        
        # Score each agent based on keyword matches
        scored_agents = []
        for agent in all_agents:
            score = 0
            
            # Check capabilities
            for capability in agent.capabilities:
                if capability.lower() in keywords:
                    score += 3  # High weight for capability match
            
            # Check description
            if agent.description:
                desc_lower = agent.description.lower()
                for keyword in keywords:
                    if keyword in desc_lower:
                        score += 1  # Lower weight for description match
            
            # Check agent name
            name_lower = agent.name.lower()
            for keyword in keywords:
                if keyword in name_lower:
                    score += 2  # Medium weight for name match
            
            if score > 0:
                scored_agents.append((score, agent))
        
        # Sort by score (descending) and return agents
        scored_agents.sort(key=lambda x: x[0], reverse=True)
        return [agent for score, agent in scored_agents]
    
    async def get_agent_details(
        self,
        agent_name: str
    ) -> Optional[AgentMetadata]:
        """
        Get details for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent metadata or None if not found
        """
        # Check cache first
        cache_key = f"agent_{agent_name}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # Query database
        agent = await self.repository.get_by_name(agent_name)
        
        if agent is None:
            return None
        
        # Convert to metadata
        agent_metadata = AgentMetadata.from_agent(agent)
        
        # Cache result
        self._set_cache(cache_key, agent_metadata)
        
        return agent_metadata
    
    def format_agents_for_llm(
        self,
        agents: List[AgentMetadata]
    ) -> str:
        """
        Format agent list for LLM prompt.
        
        Creates a structured, readable format that helps the LLM understand
        available agents and their capabilities.
        
        Args:
            agents: List of agents to format
            
        Returns:
            Formatted string for LLM
        """
        if not agents:
            return "No agents available."
        
        lines = ["Available Agents:", ""]
        
        for i, agent in enumerate(agents, 1):
            lines.append(f"{i}. Agent: {agent.name}")
            lines.append(f"   URL: {agent.url}")
            lines.append(f"   Status: {agent.status}")
            
            if agent.description:
                lines.append(f"   Description: {agent.description}")
            
            if agent.capabilities:
                caps = ", ".join(agent.capabilities)
                lines.append(f"   Capabilities: {caps}")
            
            lines.append("")  # Blank line between agents
        
        return "\n".join(lines)
