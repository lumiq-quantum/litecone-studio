"""Agent database model for the Workflow Management API."""

from sqlalchemy import Column, String, Integer, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from api.database import Base


class Agent(Base):
    """
    Agent model representing external services that execute workflow steps.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Unique agent name
        url: Agent endpoint URL
        description: Optional description of the agent
        auth_type: Authentication type ('none', 'bearer', 'apikey')
        auth_config: JSON configuration for authentication
        timeout_ms: Request timeout in milliseconds
        retry_config: JSON configuration for retry behavior
        status: Agent status ('active', 'inactive', 'deleted')
        created_at: Timestamp when agent was created
        updated_at: Timestamp when agent was last updated
        created_by: User who created the agent
        updated_by: User who last updated the agent
    """
    
    __tablename__ = "agents"
    
    # Core fields
    name = Column(String(255), unique=True, nullable=False, index=True)
    url = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    
    # Authentication configuration
    auth_type = Column(String(50), nullable=True, default="none")
    auth_config = Column(JSONB, nullable=True)
    
    # Timeout and retry configuration
    timeout_ms = Column(Integer, nullable=False, default=30000)
    retry_config = Column(JSONB, nullable=True)
    
    # Status and audit fields
    status = Column(String(50), nullable=False, default="active", index=True)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_agents_name", "name"),
        Index("idx_agents_status", "status"),
    )
    
    def __repr__(self) -> str:
        """String representation of Agent."""
        return f"<Agent(id={self.id}, name='{self.name}', status='{self.status}')>"
