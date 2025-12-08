"""Workflow API client for creating workflows via the workflow management API."""

import logging
from typing import Dict, Any, Optional
from uuid import UUID
import httpx

from api.config import settings

logger = logging.getLogger(__name__)


class WorkflowAPIClient:
    """
    Client for interacting with the workflow management API.
    
    This client provides methods to create workflows via the workflow API,
    implementing requirements 6.1-6.5 for workflow save functionality.
    """
    
    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize the workflow API client.
        
        Args:
            base_url: Base URL for the API (defaults to local API)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or f"http://{settings.host}:{settings.port}{settings.api_prefix}"
        self.timeout = timeout
        logger.info(f"Initialized WorkflowAPIClient with base_url: {self.base_url}")
    
    def _generate_unique_name(self, base_name: str, attempt: int = 0) -> str:
        """
        Generate a unique workflow name.
        
        This method implements name generation logic that adds suffixes
        for conflict resolution.
        
        Args:
            base_name: Base name for the workflow
            attempt: Attempt number for conflict resolution
            
        Returns:
            Generated workflow name
            
        Requirements:
        - 6.2: Implements unique name generation logic
        """
        if attempt == 0:
            return base_name
        return f"{base_name}-{attempt}"
    
    async def create_workflow(
        self,
        workflow_json: Dict[str, Any],
        name: str,
        description: Optional[str] = None,
        max_retries: int = 5
    ) -> Dict[str, Any]:
        """
        Create a workflow via the workflow API.
        
        This method creates a workflow definition by calling the workflow API.
        It implements name conflict resolution by retrying with modified names
        if conflicts occur.
        
        Args:
            workflow_json: Complete workflow definition
            name: Desired workflow name
            description: Optional workflow description
            max_retries: Maximum number of retry attempts for name conflicts
            
        Returns:
            Dictionary containing:
                - workflow_id: UUID of the created workflow
                - name: Final workflow name used
                - version: Workflow version number
                - link: URL to view the workflow
                
        Raises:
            ValueError: If workflow creation fails after all retries
            httpx.HTTPError: If API request fails
            
        Requirements:
        - 6.1: Creates workflow via workflow API
        - 6.2: Implements unique name generation
        - 6.3: Implements name conflict resolution
        - 6.4: Returns workflow ID and link
        - 6.5: Implements error handling and retry logic
        """
        attempt = 0
        last_error = None
        
        while attempt < max_retries:
            try:
                # Generate name for this attempt
                current_name = self._generate_unique_name(name, attempt)
                
                # Prepare request payload
                payload = {
                    "name": current_name,
                    "description": description or f"AI-generated workflow: {current_name}",
                    "start_step": workflow_json.get("start_step"),
                    "steps": workflow_json.get("steps", {})
                }
                
                logger.info(f"Attempting to create workflow '{current_name}' (attempt {attempt + 1}/{max_retries})")
                
                # Make API request
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/workflows",
                        json=payload
                    )
                    
                    # Check for success
                    if response.status_code == 201:
                        result = response.json()
                        workflow_id = result.get("id")
                        
                        logger.info(f"Successfully created workflow '{current_name}' with ID: {workflow_id}")
                        
                        # Generate link to view the workflow
                        link = f"{self.base_url}/workflows/{workflow_id}"
                        
                        return {
                            "workflow_id": workflow_id,
                            "name": current_name,
                            "version": result.get("version", 1),
                            "link": link,
                            "status": result.get("status", "active")
                        }
                    
                    # Handle name conflict (400 with specific error)
                    elif response.status_code == 400:
                        error_detail = response.json().get("detail", "")
                        
                        # Check if it's a name conflict
                        if "name" in error_detail.lower() and ("exists" in error_detail.lower() or "duplicate" in error_detail.lower()):
                            logger.warning(f"Name conflict for '{current_name}', retrying with different name")
                            attempt += 1
                            last_error = f"Name conflict: {error_detail}"
                            continue
                        else:
                            # Other validation error, don't retry
                            logger.error(f"Validation error creating workflow: {error_detail}")
                            raise ValueError(f"Workflow validation failed: {error_detail}")
                    
                    # Handle other errors
                    else:
                        error_detail = response.json().get("detail", response.text)
                        logger.error(f"API error creating workflow: {response.status_code} - {error_detail}")
                        raise ValueError(f"Failed to create workflow: {error_detail}")
                        
            except httpx.TimeoutException as e:
                logger.error(f"Timeout creating workflow: {e}")
                raise ValueError(f"Request timeout while creating workflow: {str(e)}")
            
            except httpx.RequestError as e:
                logger.error(f"Request error creating workflow: {e}")
                raise ValueError(f"Failed to connect to workflow API: {str(e)}")
            
            except ValueError:
                # Re-raise ValueError (validation errors)
                raise
            
            except Exception as e:
                logger.error(f"Unexpected error creating workflow: {e}", exc_info=True)
                raise ValueError(f"Unexpected error creating workflow: {str(e)}")
        
        # If we exhausted all retries
        error_msg = f"Failed to create workflow after {max_retries} attempts. Last error: {last_error}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    async def get_workflow(self, workflow_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get workflow details by ID.
        
        Args:
            workflow_id: UUID of the workflow
            
        Returns:
            Workflow details or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/workflows/{workflow_id}"
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    logger.error(f"Error getting workflow: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting workflow: {e}")
            return None

