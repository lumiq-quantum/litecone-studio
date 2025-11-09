"""Workflow service for managing workflow lifecycle and operations."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from api.repositories.workflow import WorkflowRepository
from api.repositories.agent import AgentRepository
from api.services.audit import AuditService
from api.schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowStepSchema
from api.models.workflow import WorkflowDefinition


class WorkflowService:
    """
    Service for managing workflow definitions.
    
    This service provides business logic for workflow operations including
    creation, retrieval, updates, deletion, and validation of workflow
    structures and agent references.
    
    Requirements:
    - 2.1: Create workflow via POST /api/v1/workflows
    - 2.2: List workflows via GET /api/v1/workflows with pagination and filtering
    - 2.3: Get workflow details via GET /api/v1/workflows/{workflow_id}
    - 2.4: Update workflow via PUT /api/v1/workflows/{workflow_id}
    - 2.5: Delete workflow via DELETE /api/v1/workflows/{workflow_id}
    - 2.6: Get workflow versions via GET /api/v1/workflows/{workflow_id}/versions
    - 8.5: Validate workflow structure before saving
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize WorkflowService with database session.
        
        Args:
            db: Async database session
        """
        self.repository = WorkflowRepository(db)
        self.agent_repository = AgentRepository(db)
        self.audit_service = AuditService(db)
    
    async def create_workflow(
        self,
        workflow_data: WorkflowCreate,
        user_id: Optional[str] = None
    ) -> WorkflowDefinition:
        """
        Create a new workflow definition with validation and audit logging.
        
        This method validates that all referenced agents exist and are active,
        validates the workflow structure (no cycles, all steps reachable),
        creates the workflow in the database, and logs the action.
        
        Args:
            workflow_data: Workflow creation data
            user_id: Identifier of the user creating the workflow
        
        Returns:
            Created WorkflowDefinition instance
        
        Raises:
            ValueError: If validation fails (agents not found, invalid structure)
        
        Example:
            workflow = await workflow_service.create_workflow(
                workflow_data=WorkflowCreate(
                    name="data-pipeline",
                    description="ETL pipeline",
                    start_step="extract",
                    steps={
                        "extract": WorkflowStepSchema(
                            id="extract",
                            agent_name="DataExtractor",
                            next_step="transform",
                            input_mapping={"source": "${workflow.input.source}"}
                        ),
                        "transform": WorkflowStepSchema(
                            id="transform",
                            agent_name="DataTransformer",
                            next_step=None,
                            input_mapping={"data": "${extract.output.data}"}
                        )
                    }
                ),
                user_id="admin@example.com"
            )
        
        Requirements:
        - 2.1: Creates workflow record in database via POST endpoint
        - 8.5: Validates workflow structure before saving
        """
        # Validate that all agents exist and are active
        await self.validate_agents(workflow_data.steps)
        
        # Validate workflow structure (already done by Pydantic, but explicit check)
        self.validate_workflow_structure(workflow_data)
        
        # Check if workflow with same name already exists
        existing_workflows = await self.repository.list_versions(workflow_data.name, limit=1)
        if existing_workflows:
            # Get the latest version and increment
            latest_version = existing_workflows[0].version
            version = latest_version + 1
        else:
            version = 1
        
        # Prepare workflow data for storage
        workflow_dict = {
            "name": workflow_data.name,
            "description": workflow_data.description,
            "version": version,
            "workflow_data": {
                "workflow_id": f"wf-{workflow_data.name}-{version}",
                "name": workflow_data.name,
                "version": str(version),
                "start_step": workflow_data.start_step,
                "steps": {
                    step_id: {
                        "id": step.id,
                        "agent_name": step.agent_name,
                        "next_step": step.next_step,
                        "input_mapping": step.input_mapping
                    }
                    for step_id, step in workflow_data.steps.items()
                }
            },
            "status": "active",
            "created_by": user_id,
            "updated_by": user_id
        }
        
        # Create workflow
        workflow = await self.repository.create(workflow_dict)
        
        # Log the creation action
        await self.audit_service.log_action(
            entity_type="workflow",
            entity_id=workflow.id,
            action="create",
            user_id=user_id,
            changes=workflow_data.model_dump()
        )
        
        return workflow
    
    async def validate_agents(self, steps: Dict[str, WorkflowStepSchema]) -> None:
        """
        Validate that all referenced agents exist and are active.
        
        This method checks that every agent referenced in the workflow steps
        exists in the database and has an 'active' status.
        
        Args:
            steps: Dictionary of step definitions
        
        Raises:
            ValueError: If any agent is not found or not active
        
        Example:
            await workflow_service.validate_agents({
                "step1": WorkflowStepSchema(
                    id="step1",
                    agent_name="MyAgent",
                    next_step=None,
                    input_mapping={}
                )
            })
        
        Requirements:
        - 8.5: Validates agent references before saving workflow
        """
        # Extract unique agent names from steps
        agent_names = {step.agent_name for step in steps.values()}
        
        # Validate each agent
        for agent_name in agent_names:
            agent = await self.agent_repository.get_by_name(agent_name)
            if not agent:
                raise ValueError(f"Agent '{agent_name}' not found")
            if agent.status != 'active':
                raise ValueError(f"Agent '{agent_name}' is not active (status: {agent.status})")
    
    def validate_workflow_structure(self, workflow_data: WorkflowCreate) -> None:
        """
        Validate workflow structure for correctness.
        
        This method validates:
        - start_step exists in steps
        - No circular references (cycles)
        - All steps are reachable from start_step
        
        Note: Most validation is already performed by Pydantic validators
        in WorkflowCreate schema. This method serves as an explicit
        validation point and can be extended with additional checks.
        
        Args:
            workflow_data: Workflow creation data
        
        Raises:
            ValueError: If workflow structure is invalid
        
        Example:
            workflow_service.validate_workflow_structure(workflow_data)
        
        Requirements:
        - 8.5: Validates workflow structure (no cycles, valid references)
        """
        # Pydantic already validates:
        # - start_step exists in steps
        # - no circular references
        # - all steps are reachable
        # - next_step references are valid
        
        # Additional validation can be added here if needed
        # For now, we rely on Pydantic's comprehensive validation
        
        # Verify at least one step exists
        if not workflow_data.steps:
            raise ValueError("Workflow must have at least one step")
        
        # Verify start_step is set
        if not workflow_data.start_step:
            raise ValueError("Workflow must have a start_step defined")
    
    async def get_workflow(self, workflow_id: UUID) -> Optional[WorkflowDefinition]:
        """
        Get workflow by ID.
        
        Args:
            workflow_id: UUID of the workflow to retrieve
        
        Returns:
            WorkflowDefinition instance or None if not found
        
        Example:
            workflow = await workflow_service.get_workflow(workflow_id)
            if workflow:
                print(f"Found workflow: {workflow.name} v{workflow.version}")
        
        Requirements:
        - 2.3: Returns workflow details via GET endpoint
        """
        return await self.repository.get_by_id(workflow_id)
    
    async def get_workflow_by_name_and_version(
        self,
        name: str,
        version: int
    ) -> Optional[WorkflowDefinition]:
        """
        Get workflow by name and version.
        
        Args:
            name: Workflow name
            version: Workflow version
        
        Returns:
            WorkflowDefinition instance or None if not found
        
        Example:
            workflow = await workflow_service.get_workflow_by_name_and_version(
                "data-pipeline", 2
            )
        """
        return await self.repository.get_by_name_and_version(name, version)
    
    async def list_workflows(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        name: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[WorkflowDefinition]:
        """
        List workflows with pagination, filtering, and sorting.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            status: Optional status filter ('active', 'inactive', 'deleted')
            name: Optional name filter (exact match)
            sort_by: Field to sort by ('name', 'created_at', 'updated_at', 'version')
            sort_order: Sort order ('asc' or 'desc')
        
        Returns:
            List of WorkflowDefinition instances
        
        Example:
            # Get first page of active workflows
            workflows = await workflow_service.list_workflows(
                skip=0,
                limit=20,
                status="active",
                sort_by="name",
                sort_order="asc"
            )
        
        Requirements:
        - 2.2: Returns paginated list of workflows via GET endpoint
        """
        return await self.repository.list(
            skip=skip,
            limit=limit,
            status=status,
            name=name,
            sort_by=sort_by,
            sort_order=sort_order
        )
    
    async def update_workflow(
        self,
        workflow_id: UUID,
        workflow_data: WorkflowUpdate,
        user_id: Optional[str] = None
    ) -> WorkflowDefinition:
        """
        Update an existing workflow and log the action.
        
        This method updates a workflow's configuration, validates any
        structural changes, increments the version, and logs the action.
        
        Args:
            workflow_id: UUID of the workflow to update
            workflow_data: Workflow update data
            user_id: Identifier of the user updating the workflow
        
        Returns:
            Updated WorkflowDefinition instance
        
        Raises:
            ValueError: If workflow not found or validation fails
        
        Example:
            updated_workflow = await workflow_service.update_workflow(
                workflow_id=workflow_id,
                workflow_data=WorkflowUpdate(
                    description="Updated description",
                    status="inactive"
                ),
                user_id="admin@example.com"
            )
        
        Requirements:
        - 2.4: Updates workflow configuration via PUT endpoint
        - 8.5: Validates workflow structure before saving
        """
        # Check if workflow exists
        existing_workflow = await self.repository.get_by_id(workflow_id)
        if not existing_workflow:
            raise ValueError(f"Workflow with id '{workflow_id}' not found")
        
        # If steps are being updated, validate agents
        if workflow_data.steps is not None:
            await self.validate_agents(workflow_data.steps)
        
        # Prepare update data
        update_dict = workflow_data.model_dump(exclude_unset=True)
        
        # If workflow structure is being updated, increment version and update workflow_data
        if workflow_data.steps is not None or workflow_data.start_step is not None:
            # Increment version
            new_version = existing_workflow.version + 1
            update_dict["version"] = new_version
            
            # Build updated workflow_data
            updated_workflow_data = existing_workflow.workflow_data.copy()
            updated_workflow_data["version"] = str(new_version)
            
            if workflow_data.start_step is not None:
                updated_workflow_data["start_step"] = workflow_data.start_step
            
            if workflow_data.steps is not None:
                updated_workflow_data["steps"] = {
                    step_id: {
                        "id": step.id,
                        "agent_name": step.agent_name,
                        "next_step": step.next_step,
                        "input_mapping": step.input_mapping
                    }
                    for step_id, step in workflow_data.steps.items()
                }
            
            update_dict["workflow_data"] = updated_workflow_data
        
        # Set updated_by
        update_dict["updated_by"] = user_id
        
        # Update workflow
        workflow = await self.repository.update(workflow_id, update_dict)
        
        # Log the update action
        await self.audit_service.log_action(
            entity_type="workflow",
            entity_id=workflow_id,
            action="update",
            user_id=user_id,
            changes=workflow_data.model_dump(exclude_unset=True)
        )
        
        return workflow
    
    async def delete_workflow(
        self,
        workflow_id: UUID,
        user_id: Optional[str] = None
    ) -> None:
        """
        Soft delete a workflow and log the action.
        
        This method marks a workflow as deleted (soft delete) to prevent
        it from being used in new executions while preserving historical data.
        
        Args:
            workflow_id: UUID of the workflow to delete
            user_id: Identifier of the user deleting the workflow
        
        Raises:
            ValueError: If workflow not found
        
        Example:
            await workflow_service.delete_workflow(
                workflow_id=workflow_id,
                user_id="admin@example.com"
            )
        
        Requirements:
        - 2.5: Soft-deletes workflow via DELETE endpoint
        """
        # Check if workflow exists
        existing_workflow = await self.repository.get_by_id(workflow_id)
        if not existing_workflow:
            raise ValueError(f"Workflow with id '{workflow_id}' not found")
        
        # Soft delete workflow
        await self.repository.soft_delete(workflow_id, deleted_by=user_id)
        
        # Log the deletion action
        await self.audit_service.log_action(
            entity_type="workflow",
            entity_id=workflow_id,
            action="delete",
            user_id=user_id
        )
    
    async def get_versions(
        self,
        workflow_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[WorkflowDefinition]:
        """
        Get all versions of a workflow.
        
        This method retrieves all versions of a workflow by its name,
        ordered by version number (newest first).
        
        Args:
            workflow_id: UUID of any version of the workflow
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
        
        Returns:
            List of WorkflowDefinition instances ordered by version descending
        
        Raises:
            ValueError: If workflow not found
        
        Example:
            versions = await workflow_service.get_versions(workflow_id)
            for version in versions:
                print(f"Version {version.version}: {version.updated_at}")
        
        Requirements:
        - 2.6: Returns all versions via GET /api/v1/workflows/{workflow_id}/versions
        """
        # Get the workflow to find its name
        workflow = await self.repository.get_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow with id '{workflow_id}' not found")
        
        # Get all versions by name
        return await self.repository.list_versions(
            name=workflow.name,
            skip=skip,
            limit=limit
        )
