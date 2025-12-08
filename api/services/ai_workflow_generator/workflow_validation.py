"""Workflow validation service for validating generated workflows."""

from typing import Dict, Any, List, Optional, Set
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
import copy

from api.schemas.workflow import WorkflowCreate, WorkflowStepSchema
from api.services.ai_workflow_generator.agent_query import AgentQueryService
from api.services.ai_workflow_generator.schema_loader import SchemaLoader


class ValidationResult:
    """Result of workflow validation."""
    
    def __init__(
        self,
        is_valid: bool,
        errors: List[str],
        warnings: List[str],
        auto_corrections: List[str],
        corrected_workflow: Optional[Dict[str, Any]] = None
    ):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings
        self.auto_corrections = auto_corrections
        self.corrected_workflow = corrected_workflow
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "auto_corrections": self.auto_corrections
        }


class WorkflowValidationService:
    """Service for validating workflow JSON structures."""
    
    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        schema_loader: Optional[SchemaLoader] = None
    ):
        """
        Initialize the workflow validation service.
        
        Args:
            db: Optional database session for agent validation
            schema_loader: Optional schema loader for dynamic validation.
                          If None, creates a new instance.
        """
        self.db = db
        self.agent_query_service = AgentQueryService(db) if db else None
        self.schema_loader = schema_loader or SchemaLoader()
    
    async def validate_workflow(
        self,
        workflow_json: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate a workflow JSON structure.
        
        Performs comprehensive validation including:
        - Schema validation
        - Cycle detection
        - Reachability analysis
        - Agent reference validation
        
        Args:
            workflow_json: Workflow to validate
            
        Returns:
            ValidationResult with errors, warnings, and auto-corrections
        """
        errors = []
        warnings = []
        auto_corrections = []
        
        # Make a copy for potential auto-correction
        corrected_workflow = copy.deepcopy(workflow_json)
        
        # 1. Validate schema
        schema_errors = self.validate_schema(corrected_workflow)
        errors.extend(schema_errors)
        
        # If schema validation fails, try auto-correction
        if schema_errors:
            try:
                corrected_workflow = self.auto_correct(corrected_workflow, schema_errors)
                # Re-validate after correction
                schema_errors_after = self.validate_schema(corrected_workflow)
                if not schema_errors_after:
                    auto_corrections.append("Auto-corrected schema validation errors")
                    errors = []  # Clear errors if auto-correction succeeded
            except Exception as e:
                errors.append(f"Auto-correction failed: {str(e)}")
        
        # Only proceed with further validation if schema is valid
        if not errors:
            # 2. Detect cycles
            cycle_errors = self.detect_cycles(corrected_workflow)
            errors.extend(cycle_errors)
            
            # 3. Check reachability
            reachability_errors = self.check_reachability(corrected_workflow)
            errors.extend(reachability_errors)
            
            # 4. Validate agent references (if agent service available)
            if self.agent_query_service:
                agent_errors = await self.validate_agent_references(corrected_workflow)
                errors.extend(agent_errors)
            else:
                warnings.append("Agent reference validation skipped (no database session)")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            auto_corrections=auto_corrections,
            corrected_workflow=corrected_workflow
        )
    
    def validate_schema(
        self,
        workflow_json: Dict[str, Any],
        schema_version: Optional[str] = None
    ) -> List[str]:
        """
        Validate workflow against JSON schema.
        
        Uses dynamic schema loading to support schema evolution.
        Falls back to Pydantic validation if schema loader fails.
        
        Args:
            workflow_json: Workflow to validate
            schema_version: Optional specific schema version to use.
                          If None, auto-detects the appropriate version.
            
        Returns:
            List of schema validation errors
        """
        errors = []
        
        try:
            # Try JSON schema validation first (supports schema evolution)
            schema_errors = self.schema_loader.validate(
                workflow_json,
                version_string=schema_version
            )
            errors.extend(schema_errors)
            
            # If JSON schema validation passes, also validate with Pydantic
            # for additional type checking and business logic validation
            if not schema_errors:
                try:
                    WorkflowCreate(**workflow_json)
                except ValidationError as e:
                    for error in e.errors():
                        loc = " -> ".join(str(x) for x in error['loc'])
                        msg = error['msg']
                        errors.append(f"Schema error at {loc}: {msg}")
        
        except Exception as e:
            # If schema loader fails, fall back to Pydantic validation
            errors.append(f"Schema loader error: {str(e)}")
            try:
                WorkflowCreate(**workflow_json)
            except ValidationError as e:
                for error in e.errors():
                    loc = " -> ".join(str(x) for x in error['loc'])
                    msg = error['msg']
                    errors.append(f"Schema error at {loc}: {msg}")
            except Exception as e2:
                errors.append(f"Unexpected validation error: {str(e2)}")
        
        return errors
    
    def detect_cycles(
        self,
        workflow_json: Dict[str, Any]
    ) -> List[str]:
        """
        Detect circular references in workflow using DFS.
        
        Args:
            workflow_json: Workflow to check
            
        Returns:
            List of cycle errors with step paths
        """
        errors = []
        
        steps = workflow_json.get('steps', {})
        if not steps:
            return errors
        
        visited: Set[str] = set()
        current_path: Set[str] = set()
        cycle_found = False
        
        def dfs(step_id: str, path: List[str]) -> Optional[List[str]]:
            """DFS to detect cycles, returns cycle path if found."""
            nonlocal cycle_found
            
            if step_id in current_path:
                # Found a cycle
                cycle_start_idx = path.index(step_id)
                return path[cycle_start_idx:] + [step_id]
            
            if step_id in visited:
                return None
            
            visited.add(step_id)
            current_path.add(step_id)
            path.append(step_id)
            
            step = steps.get(step_id, {})
            
            # Check next_step
            next_step = step.get('next_step')
            if next_step and next_step in steps:
                cycle_path = dfs(next_step, path.copy())
                if cycle_path:
                    return cycle_path
            
            # Check parallel steps
            step_type = step.get('type', 'agent')
            if step_type == 'parallel':
                parallel_steps = step.get('parallel_steps', [])
                for parallel_step in parallel_steps:
                    if parallel_step in steps:
                        cycle_path = dfs(parallel_step, path.copy())
                        if cycle_path:
                            return cycle_path
            
            # Check conditional branches
            if step_type == 'conditional':
                if_true = step.get('if_true_step')
                if_false = step.get('if_false_step')
                
                if if_true and if_true in steps:
                    cycle_path = dfs(if_true, path.copy())
                    if cycle_path:
                        return cycle_path
                
                if if_false and if_false in steps:
                    cycle_path = dfs(if_false, path.copy())
                    if cycle_path:
                        return cycle_path
            
            # Check loop body
            if step_type == 'loop':
                loop_config = step.get('loop_config', {})
                loop_body = loop_config.get('loop_body', [])
                for loop_step in loop_body:
                    if loop_step in steps:
                        cycle_path = dfs(loop_step, path.copy())
                        if cycle_path:
                            return cycle_path
            
            current_path.remove(step_id)
            return None
        
        # Check for cycles starting from each step
        for step_id in steps:
            visited.clear()
            current_path.clear()
            cycle_path = dfs(step_id, [])
            if cycle_path:
                cycle_str = " -> ".join(cycle_path)
                errors.append(f"Circular reference detected: {cycle_str}")
                break  # Report first cycle found
        
        return errors
    
    def check_reachability(
        self,
        workflow_json: Dict[str, Any]
    ) -> List[str]:
        """
        Check that all steps are reachable from start_step using BFS.
        
        Args:
            workflow_json: Workflow to check
            
        Returns:
            List of unreachable step IDs
        """
        errors = []
        
        start_step = workflow_json.get('start_step')
        steps = workflow_json.get('steps', {})
        
        if not start_step or not steps:
            return errors
        
        if start_step not in steps:
            errors.append(f"Start step '{start_step}' not found in workflow steps")
            return errors
        
        # BFS to find all reachable steps
        reachable: Set[str] = set()
        to_visit = [start_step]
        
        while to_visit:
            current = to_visit.pop(0)
            
            if current in reachable:
                continue
            
            reachable.add(current)
            step = steps.get(current)
            
            if not step:
                continue
            
            # Add next_step
            next_step = step.get('next_step')
            if next_step and next_step in steps:
                to_visit.append(next_step)
            
            # Add parallel steps
            step_type = step.get('type', 'agent')
            if step_type == 'parallel':
                parallel_steps = step.get('parallel_steps', [])
                for parallel_step in parallel_steps:
                    if parallel_step in steps:
                        to_visit.append(parallel_step)
            
            # Add conditional branches
            if step_type == 'conditional':
                if_true = step.get('if_true_step')
                if_false = step.get('if_false_step')
                
                if if_true and if_true in steps:
                    to_visit.append(if_true)
                if if_false and if_false in steps:
                    to_visit.append(if_false)
            
            # Add loop body steps
            if step_type == 'loop':
                loop_config = step.get('loop_config', {})
                loop_body = loop_config.get('loop_body', [])
                for loop_step in loop_body:
                    if loop_step in steps:
                        to_visit.append(loop_step)
        
        # Find unreachable steps
        all_steps = set(steps.keys())
        unreachable = all_steps - reachable
        
        if unreachable:
            unreachable_list = sorted(unreachable)
            errors.append(
                f"Unreachable steps detected: {', '.join(unreachable_list)}. "
                f"All steps must be reachable from start_step '{start_step}'"
            )
        
        return errors
    
    async def validate_agent_references(
        self,
        workflow_json: Dict[str, Any]
    ) -> List[str]:
        """
        Validate that all agent references exist and are active.
        
        Args:
            workflow_json: Workflow to validate
            
        Returns:
            List of invalid agent references
        """
        errors = []
        
        if not self.agent_query_service:
            return errors
        
        steps = workflow_json.get('steps', {})
        if not steps:
            return errors
        
        # Collect all agent names referenced in the workflow
        agent_names = set()
        for step_id, step in steps.items():
            step_type = step.get('type', 'agent')
            if step_type == 'agent':
                agent_name = step.get('agent_name')
                if agent_name:
                    agent_names.add(agent_name)
        
        # Validate each agent exists and is active
        for agent_name in agent_names:
            agent = await self.agent_query_service.get_agent_details(agent_name)
            
            if agent is None:
                errors.append(f"Agent '{agent_name}' not found in registry")
            elif agent.status != 'active':
                errors.append(f"Agent '{agent_name}' is not active (status: {agent.status})")
        
        return errors
    
    def auto_correct(
        self,
        workflow_json: Dict[str, Any],
        errors: List[str]
    ) -> Dict[str, Any]:
        """
        Attempt to auto-correct common validation errors.
        
        Common corrections:
        - Add missing required fields with defaults
        - Fix step ID mismatches
        - Add missing input_mapping for agent steps
        - Remove invalid next_step references
        
        Args:
            workflow_json: Workflow with errors
            errors: List of errors to correct
            
        Returns:
            Corrected workflow JSON
        """
        corrected = copy.deepcopy(workflow_json)
        
        # Ensure required top-level fields exist
        if 'name' not in corrected:
            corrected['name'] = 'untitled-workflow'
        
        if 'start_step' not in corrected and 'steps' in corrected:
            # Set first step as start_step
            steps = corrected['steps']
            if steps:
                corrected['start_step'] = list(steps.keys())[0]
        
        if 'steps' not in corrected:
            corrected['steps'] = {}
        
        # Fix step-level issues
        steps = corrected.get('steps', {})
        for step_id, step in list(steps.items()):
            # Ensure step has an 'id' field matching the key
            if 'id' not in step:
                step['id'] = step_id
            elif step['id'] != step_id:
                step['id'] = step_id
            
            # Ensure step has a type
            if 'type' not in step:
                step['type'] = 'agent'
            
            step_type = step.get('type', 'agent')
            
            # Fix agent steps
            if step_type == 'agent':
                # Ensure agent_name exists
                if 'agent_name' not in step or not step['agent_name']:
                    step['agent_name'] = 'default-agent'
                
                # Ensure input_mapping exists
                if 'input_mapping' not in step:
                    step['input_mapping'] = {}
            
            # Remove invalid next_step references
            next_step = step.get('next_step')
            if next_step and next_step not in steps:
                step['next_step'] = None
            
            # Fix parallel steps
            if step_type == 'parallel':
                if 'parallel_steps' not in step or not step.get('parallel_steps'):
                    # Can't auto-fix this meaningfully, but ensure field exists
                    step['parallel_steps'] = []
            
            # Fix conditional steps
            if step_type == 'conditional':
                if 'condition' not in step:
                    step['condition'] = {'expression': 'true'}
                
                # Remove invalid branch references
                if_true = step.get('if_true_step')
                if_false = step.get('if_false_step')
                
                if if_true and if_true not in steps:
                    step['if_true_step'] = None
                if if_false and if_false not in steps:
                    step['if_false_step'] = None
            
            # Fix loop steps
            if step_type == 'loop':
                if 'loop_config' not in step:
                    step['loop_config'] = {
                        'collection': '${workflow.input.items}',
                        'loop_body': []
                    }
        
        return corrected
    
    def detect_schema_version(self, workflow_json: Dict[str, Any]) -> str:
        """
        Detect the appropriate schema version for a workflow.
        
        Args:
            workflow_json: Workflow to analyze
            
        Returns:
            Detected schema version string
        """
        schema = self.schema_loader.detect_version(workflow_json)
        return schema.version_string
    
    def get_available_schema_versions(self) -> List[str]:
        """
        Get list of available schema versions.
        
        Returns:
            List of version strings
        """
        return self.schema_loader.get_available_versions()
    
    def get_latest_schema_version(self) -> str:
        """
        Get the latest schema version.
        
        Returns:
            Latest version string
        """
        return self.schema_loader.get_latest_version()
    
    async def validate_with_version(
        self,
        workflow_json: Dict[str, Any],
        schema_version: str
    ) -> ValidationResult:
        """
        Validate workflow against a specific schema version.
        
        This method supports schema evolution by allowing validation
        against different schema versions.
        
        Args:
            workflow_json: Workflow to validate
            schema_version: Specific schema version to validate against
            
        Returns:
            ValidationResult with errors, warnings, and auto-corrections
        """
        errors = []
        warnings = []
        auto_corrections = []
        
        # Make a copy for potential auto-correction
        corrected_workflow = copy.deepcopy(workflow_json)
        
        # Validate schema with specific version
        schema_errors = self.validate_schema(corrected_workflow, schema_version)
        errors.extend(schema_errors)
        
        # If schema validation fails, try auto-correction
        if schema_errors:
            try:
                corrected_workflow = self.auto_correct(corrected_workflow, schema_errors)
                # Re-validate after correction
                schema_errors_after = self.validate_schema(
                    corrected_workflow,
                    schema_version
                )
                if not schema_errors_after:
                    auto_corrections.append(
                        f"Auto-corrected schema validation errors for version {schema_version}"
                    )
                    errors = []  # Clear errors if auto-correction succeeded
            except Exception as e:
                errors.append(f"Auto-correction failed: {str(e)}")
        
        # Only proceed with further validation if schema is valid
        if not errors:
            # Detect cycles
            cycle_errors = self.detect_cycles(corrected_workflow)
            errors.extend(cycle_errors)
            
            # Check reachability
            reachability_errors = self.check_reachability(corrected_workflow)
            errors.extend(reachability_errors)
            
            # Validate agent references (if agent service available)
            if self.agent_query_service:
                agent_errors = await self.validate_agent_references(corrected_workflow)
                errors.extend(agent_errors)
            else:
                warnings.append("Agent reference validation skipped (no database session)")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            auto_corrections=auto_corrections,
            corrected_workflow=corrected_workflow
        )
