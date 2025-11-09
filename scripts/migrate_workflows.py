#!/usr/bin/env python3
"""
Workflow Migration Script

Imports existing workflow JSON files into the Workflow Management API database.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import httpx


class WorkflowMigrator:
    def __init__(self, api_url: str, api_key: Optional[str] = None, verbose: bool = False):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.verbose = verbose
        self.headers = {'Content-Type': 'application/json'}
        if api_key:
            self.headers['X-API-Key'] = api_key
    
    def log(self, message: str, level: str = 'INFO'):
        """Log message if verbose mode is enabled"""
        if self.verbose or level == 'ERROR':
            prefix = '✓' if level == 'SUCCESS' else '✗' if level == 'ERROR' else '•'
            print(f"{prefix} {message}")
    
    def validate_workflow(self, workflow_data: Dict) -> tuple[bool, Optional[str]]:
        """Validate workflow structure"""
        required_fields = ['name', 'start_step', 'steps']
        
        for field in required_fields:
            if field not in workflow_data:
                return False, f"Missing required field: {field}"
        
        # Validate start_step exists
        if workflow_data['start_step'] not in workflow_data['steps']:
            return False, f"start_step '{workflow_data['start_step']}' not found in steps"
        
        # Validate step structure
        for step_id, step in workflow_data['steps'].items():
            if 'agent_name' not in step:
                return False, f"Step '{step_id}' missing agent_name"
            if 'input_mapping' not in step:
                return False, f"Step '{step_id}' missing input_mapping"
        
        return True, None
    
    def check_agents_exist(self, workflow_data: Dict) -> tuple[bool, List[str]]:
        """Check if all referenced agents exist in the API"""
        agent_names = {step['agent_name'] for step in workflow_data['steps'].values()}
        missing_agents = []
        
        try:
            with httpx.Client() as client:
                response = client.get(f"{self.api_url}/api/v1/agents", headers=self.headers)
                response.raise_for_status()
                registered_agents = {agent['name'] for agent in response.json().get('items', [])}
                
                for agent_name in agent_names:
                    if agent_name not in registered_agents:
                        missing_agents.append(agent_name)
            
            return len(missing_agents) == 0, missing_agents
        except Exception as e:
            self.log(f"Error checking agents: {e}", 'ERROR')
            return False, list(agent_names)
    
    def workflow_exists(self, workflow_name: str) -> bool:
        """Check if workflow already exists"""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.api_url}/api/v1/workflows",
                    params={'name': workflow_name},
                    headers=self.headers
                )
                response.raise_for_status()
                items = response.json().get('items', [])
                return len(items) > 0
        except Exception as e:
            self.log(f"Error checking workflow existence: {e}", 'ERROR')
            return False
    
    def import_workflow(self, workflow_data: Dict) -> tuple[bool, Optional[str], Optional[str]]:
        """Import workflow into API"""
        try:
            # Prepare workflow payload
            payload = {
                'name': workflow_data['name'],
                'description': workflow_data.get('description', ''),
                'start_step': workflow_data['start_step'],
                'steps': workflow_data['steps']
            }
            
            with httpx.Client() as client:
                response = client.post(
                    f"{self.api_url}/api/v1/workflows",
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                
                result = response.json()
                return True, result.get('id'), None
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get('detail', str(e)) if e.response else str(e)
            return False, None, error_detail
        except Exception as e:
            return False, None, str(e)
    
    def migrate_file(self, file_path: Path, skip_existing: bool = False) -> Dict:
        """Migrate a single workflow file"""
        result = {
            'file': file_path.name,
            'status': 'pending',
            'workflow_id': None,
            'error': None
        }
        
        try:
            # Load workflow JSON
            with open(file_path, 'r') as f:
                workflow_data = json.load(f)
            
            # Skip if not a workflow file (missing required fields)
            if 'steps' not in workflow_data:
                result['status'] = 'skipped'
                result['error'] = 'Not a workflow file'
                return result
            
            self.log(f"Validating {file_path.name}...")
            
            # Validate workflow structure
            is_valid, error = self.validate_workflow(workflow_data)
            if not is_valid:
                result['status'] = 'failed'
                result['error'] = f"Validation error: {error}"
                self.log(f"Validation failed: {error}", 'ERROR')
                return result
            
            self.log("Valid workflow structure", 'SUCCESS')
            
            # Check if workflow already exists
            if skip_existing and self.workflow_exists(workflow_data['name']):
                result['status'] = 'skipped'
                result['error'] = 'Workflow already exists'
                self.log(f"Workflow '{workflow_data['name']}' already exists, skipping")
                return result
            
            # Check agents exist
            agents_ok, missing_agents = self.check_agents_exist(workflow_data)
            if not agents_ok:
                result['status'] = 'failed'
                result['error'] = f"Missing agents: {', '.join(missing_agents)}"
                self.log(f"Missing agents: {', '.join(missing_agents)}", 'ERROR')
                return result
            
            self.log(f"All agents exist: {', '.join({step['agent_name'] for step in workflow_data['steps'].values()})}", 'SUCCESS')
            
            # Import workflow
            self.log(f"Importing {workflow_data['name']}...")
            success, workflow_id, error = self.import_workflow(workflow_data)
            
            if success:
                result['status'] = 'imported'
                result['workflow_id'] = workflow_id
                self.log(f"Created workflow: {workflow_data['name']} (ID: {workflow_id})", 'SUCCESS')
            else:
                result['status'] = 'failed'
                result['error'] = error
                self.log(f"Import failed: {error}", 'ERROR')
            
            return result
            
        except json.JSONDecodeError as e:
            result['status'] = 'failed'
            result['error'] = f"Invalid JSON: {e}"
            self.log(f"Invalid JSON in {file_path.name}: {e}", 'ERROR')
            return result
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            self.log(f"Error processing {file_path.name}: {e}", 'ERROR')
            return result
    
    def migrate_directory(self, directory: Path, skip_existing: bool = False) -> List[Dict]:
        """Migrate all workflow files in a directory"""
        results = []
        
        # Find all JSON files
        json_files = list(directory.glob('*.json'))
        
        if not json_files:
            self.log(f"No JSON files found in {directory}", 'ERROR')
            return results
        
        self.log(f"Found {len(json_files)} JSON files in {directory}")
        print()
        
        for file_path in json_files:
            result = self.migrate_file(file_path, skip_existing)
            results.append(result)
            print()  # Blank line between files
        
        return results
    
    def print_summary(self, results: List[Dict]):
        """Print migration summary"""
        total = len(results)
        imported = sum(1 for r in results if r['status'] == 'imported')
        skipped = sum(1 for r in results if r['status'] == 'skipped')
        failed = sum(1 for r in results if r['status'] == 'failed')
        
        print("=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Total files:    {total}")
        print(f"Imported:       {imported}")
        print(f"Skipped:        {skipped}")
        print(f"Failed:         {failed}")
        print()
        
        if failed > 0:
            print("Failed imports:")
            for result in results:
                if result['status'] == 'failed':
                    print(f"  • {result['file']}: {result['error']}")
            print()
        
        if imported > 0:
            print("Successfully imported:")
            for result in results:
                if result['status'] == 'imported':
                    print(f"  ✓ {result['file']} → {result['workflow_id']}")


def main():
    parser = argparse.ArgumentParser(
        description='Import workflow JSON files into Workflow Management API'
    )
    parser.add_argument(
        '--workflow-dir',
        type=str,
        required=True,
        help='Directory containing workflow JSON files'
    )
    parser.add_argument(
        '--api-url',
        type=str,
        default='http://localhost:8000',
        help='API base URL (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        help='API key for authentication (optional)'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip workflows that already exist'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate workflows without importing'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )
    
    args = parser.parse_args()
    
    # Validate directory
    workflow_dir = Path(args.workflow_dir)
    if not workflow_dir.exists():
        print(f"Error: Directory not found: {workflow_dir}", file=sys.stderr)
        sys.exit(1)
    
    if not workflow_dir.is_dir():
        print(f"Error: Not a directory: {workflow_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Check API connectivity
    try:
        with httpx.Client() as client:
            response = client.get(f"{args.api_url}/health")
            response.raise_for_status()
        print(f"✓ Connected to API at {args.api_url}")
        print()
    except Exception as e:
        print(f"✗ Cannot connect to API at {args.api_url}: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Create migrator
    migrator = WorkflowMigrator(
        api_url=args.api_url,
        api_key=args.api_key,
        verbose=args.verbose
    )
    
    if args.dry_run:
        print("DRY RUN MODE - No workflows will be imported")
        print()
    
    # Migrate workflows
    results = migrator.migrate_directory(workflow_dir, args.skip_existing)
    
    # Print summary
    migrator.print_summary(results)
    
    # Exit with error code if any imports failed
    failed_count = sum(1 for r in results if r['status'] == 'failed')
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == '__main__':
    main()
