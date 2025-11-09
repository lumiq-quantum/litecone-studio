#!/usr/bin/env python3
"""
Agent Registration Script

Registers agents from a YAML configuration file into the Workflow Management API.
"""

import argparse
import sys
from typing import Dict, List, Optional
import httpx
import yaml


class AgentRegistrar:
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
    
    def agent_exists(self, agent_name: str) -> bool:
        """Check if agent already exists"""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.api_url}/api/v1/agents",
                    headers=self.headers
                )
                response.raise_for_status()
                agents = response.json().get('items', [])
                return any(agent['name'] == agent_name for agent in agents)
        except Exception as e:
            self.log(f"Error checking agent existence: {e}", 'ERROR')
            return False
    
    def register_agent(self, agent_config: Dict) -> tuple[bool, Optional[str], Optional[str]]:
        """Register a single agent"""
        try:
            # Prepare agent payload with defaults
            payload = {
                'name': agent_config['name'],
                'url': agent_config['url'],
                'description': agent_config.get('description', ''),
                'auth_type': agent_config.get('auth_type', 'none'),
                'auth_config': agent_config.get('auth_config'),
                'timeout_ms': agent_config.get('timeout_ms', 30000),
                'retry_config': agent_config.get('retry_config', {
                    'max_retries': 3,
                    'initial_delay_ms': 1000,
                    'max_delay_ms': 30000,
                    'backoff_multiplier': 2.0
                })
            }
            
            with httpx.Client() as client:
                response = client.post(
                    f"{self.api_url}/api/v1/agents",
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
    
    def register_agents(self, config: Dict, skip_existing: bool = False) -> List[Dict]:
        """Register all agents from config"""
        results = []
        agents = config.get('agents', [])
        
        if not agents:
            self.log("No agents found in configuration", 'ERROR')
            return results
        
        self.log(f"Found {len(agents)} agents in configuration")
        print()
        
        for agent_config in agents:
            result = {
                'name': agent_config.get('name', 'unknown'),
                'status': 'pending',
                'agent_id': None,
                'error': None
            }
            
            try:
                agent_name = agent_config['name']
                self.log(f"Processing agent: {agent_name}")
                
                # Check if agent already exists
                if skip_existing and self.agent_exists(agent_name):
                    result['status'] = 'skipped'
                    result['error'] = 'Agent already exists'
                    self.log(f"Agent '{agent_name}' already exists, skipping")
                    results.append(result)
                    print()
                    continue
                
                # Register agent
                self.log(f"Registering {agent_name}...")
                success, agent_id, error = self.register_agent(agent_config)
                
                if success:
                    result['status'] = 'registered'
                    result['agent_id'] = agent_id
                    self.log(f"Registered agent: {agent_name} (ID: {agent_id})", 'SUCCESS')
                else:
                    result['status'] = 'failed'
                    result['error'] = error
                    self.log(f"Registration failed: {error}", 'ERROR')
                
            except KeyError as e:
                result['status'] = 'failed'
                result['error'] = f"Missing required field: {e}"
                self.log(f"Missing required field: {e}", 'ERROR')
            except Exception as e:
                result['status'] = 'failed'
                result['error'] = str(e)
                self.log(f"Error: {e}", 'ERROR')
            
            results.append(result)
            print()
        
        return results
    
    def print_summary(self, results: List[Dict]):
        """Print registration summary"""
        total = len(results)
        registered = sum(1 for r in results if r['status'] == 'registered')
        skipped = sum(1 for r in results if r['status'] == 'skipped')
        failed = sum(1 for r in results if r['status'] == 'failed')
        
        print("=" * 60)
        print("REGISTRATION SUMMARY")
        print("=" * 60)
        print(f"Total agents:   {total}")
        print(f"Registered:     {registered}")
        print(f"Skipped:        {skipped}")
        print(f"Failed:         {failed}")
        print()
        
        if failed > 0:
            print("Failed registrations:")
            for result in results:
                if result['status'] == 'failed':
                    print(f"  • {result['name']}: {result['error']}")
            print()
        
        if registered > 0:
            print("Successfully registered:")
            for result in results:
                if result['status'] == 'registered':
                    print(f"  ✓ {result['name']} → {result['agent_id']}")


def main():
    parser = argparse.ArgumentParser(
        description='Register agents from YAML configuration into Workflow Management API'
    )
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='YAML configuration file with agent definitions'
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
        help='Skip agents that already exist'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in configuration file: {e}", file=sys.stderr)
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
    
    # Create registrar
    registrar = AgentRegistrar(
        api_url=args.api_url,
        api_key=args.api_key,
        verbose=args.verbose
    )
    
    # Register agents
    results = registrar.register_agents(config, args.skip_existing)
    
    # Print summary
    registrar.print_summary(results)
    
    # Exit with error code if any registrations failed
    failed_count = sum(1 for r in results if r['status'] == 'failed')
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == '__main__':
    main()
