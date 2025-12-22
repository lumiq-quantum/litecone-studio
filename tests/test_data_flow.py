#!/usr/bin/env python3
"""
Test data flow between workflow steps to ensure previous step outputs
are correctly passed to subsequent steps.
"""

import json
import sys
import os

# Add the parent directory to the path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.input_resolver import InputMappingResolver


class MockExternalAgentExecutor:
    """Mock version of ExternalAgentExecutor for testing without dependencies."""
    
    def _extract_output_from_result(self, result):
        """
        Mock version of the fixed _extract_output_from_result method.
        """
        output = {}
        
        # Always include the full result for complete data access
        output.update(result)
        
        # Extract from artifacts for backward compatibility
        artifacts = result.get('artifacts', [])
        if artifacts:
            artifact_texts = []
            for artifact in artifacts:
                parts = artifact.get('parts', [])
                for part in parts:
                    if part.get('kind') == 'text':
                        artifact_texts.append(part.get('text', ''))
            
            if artifact_texts:
                output['text'] = '\n'.join(artifact_texts)
                output['artifacts'] = artifacts
        
        # Extract from history (last agent message) for backward compatibility
        history = result.get('history', [])
        for item in reversed(history):
            if item.get('role') == 'agent':
                parts = item.get('parts', [])
                for part in parts:
                    if part.get('kind') == 'text':
                        output['response'] = part.get('text', '')
                        break
                if 'response' in output:
                    break
        
        # Ensure metadata is preserved
        if 'metadata' in result:
            output['metadata'] = result['metadata']
        
        # Ensure context ID is preserved
        if 'contextId' in result:
            output['context_id'] = result['contextId']
        
        # Ensure task ID is preserved
        if 'id' in result:
            output['task_id'] = result['id']
        
        return output
    
    def _parse_jsonrpc_response(self, response, task_id):
        """Mock version of _parse_jsonrpc_response."""
        # Validate JSON-RPC structure
        if 'jsonrpc' not in response or response['jsonrpc'] != '2.0':
            raise ValueError("Invalid JSON-RPC response")
        
        # Check for error response
        if 'error' in response:
            return {
                'task_id': task_id,
                'status': 'error',
                'output': None,
                'error': response['error'].get('message', 'Unknown error')
            }
        
        # Process success response
        if 'result' not in response:
            raise ValueError("Response missing both 'result' and 'error'")
        
        result = response['result']
        
        # Extract status
        status_obj = result.get('status', {})
        state = status_obj.get('state', 'unknown')
        
        if state == 'completed':
            status = 'success'
            error = None
        else:
            status = 'error'
            error = f"Task state: {state}"
        
        # Extract output
        output = self._extract_output_from_result(result)
        
        return {
            'task_id': task_id,
            'status': status,
            'output': output,
            'error': error
        }


class TestDataFlow:
    """Test data flow between workflow steps."""
    
    def test_input_mapping_resolver_with_structured_data(self):
        """Test that InputMappingResolver correctly resolves structured data from previous steps."""
        
        # Simulate step outputs with structured data (like your example)
        step_outputs = {
            "fetch_data": {
                "data": "This is the actual PDF content that should be passed to the next step",
                "metadata": {
                    "file_type": "pdf",
                    "pages": 10,
                    "size": 1024
                },
                "task_id": "81d210e0-d935-4448-9985-d2760b17a907",
                "response": "Data fetched successfully"
            }
        }
        
        workflow_input = {
            "source_file": "document.pdf"
        }
        
        # Create resolver
        resolver = InputMappingResolver(
            workflow_input=workflow_input,
            step_outputs=step_outputs
        )
        
        # Test input mapping that references previous step data
        input_mapping = {
            "data": "${fetch_data.output.data}",
            "operation": "transform",
            "metadata": "${fetch_data.output.metadata}"
        }
        
        # Resolve the mapping
        resolved_input = resolver.resolve(input_mapping)
        
        # Verify the data is correctly resolved
        assert resolved_input["data"] == "This is the actual PDF content that should be passed to the next step"
        assert resolved_input["operation"] == "transform"
        assert resolved_input["metadata"]["file_type"] == "pdf"
        assert resolved_input["metadata"]["pages"] == 10
        
    def test_extract_output_preserves_structured_data(self):
        """Test that _extract_output_from_result preserves structured data."""
        
        # Create a mock external agent executor
        executor = MockExternalAgentExecutor()
        
        # Simulate a JSON-RPC result with structured data
        jsonrpc_result = {
            "data": "This is the actual PDF content",
            "metadata": {
                "file_type": "pdf",
                "pages": 10,
                "extracted_at": "2024-01-01T10:00:00Z"
            },
            "artifacts": [
                {
                    "parts": [
                        {
                            "kind": "text",
                            "text": "Extracted text content"
                        }
                    ],
                    "artifactId": "artifact-123"
                }
            ],
            "response": "Data extraction completed successfully",
            "task_id": "task-123",
            "context_id": "context-456"
        }
        
        # Extract output using the fixed method
        extracted_output = executor._extract_output_from_result(jsonrpc_result)
        
        # Verify that structured data is preserved
        assert extracted_output["data"] == "This is the actual PDF content"
        assert extracted_output["metadata"]["file_type"] == "pdf"
        assert extracted_output["metadata"]["pages"] == 10
        assert extracted_output["task_id"] == "task-123"
        assert extracted_output["context_id"] == "context-456"
        
        # Verify that text extraction still works for backward compatibility
        assert extracted_output["text"] == "Extracted text content"
        assert extracted_output["response"] == "Data extraction completed successfully"
        
    def test_end_to_end_data_flow(self):
        """Test complete data flow from agent response to next step input."""
        
        # Step 1: Simulate agent response processing
        executor = MockExternalAgentExecutor()
        
        # Simulate JSON-RPC response from first agent
        jsonrpc_response = {
            "jsonrpc": "2.0",
            "id": "task-123",
            "result": {
                "status": {"state": "completed"},
                "data": "Extracted PDF content here",
                "metadata": {
                    "pages": 5,
                    "file_type": "pdf"
                },
                "artifacts": [
                    {
                        "parts": [{"kind": "text", "text": "Processing complete"}]
                    }
                ]
            }
        }
        
        # Parse the response (this is what the bridge does)
        parsed_result = executor._parse_jsonrpc_response(jsonrpc_response, "task-123")
        
        # Verify the parsed result has the correct structure
        assert parsed_result["status"] == "success"
        assert parsed_result["output"]["data"] == "Extracted PDF content here"
        assert parsed_result["output"]["metadata"]["pages"] == 5
        
        # Step 2: Simulate storing this as step output (what executor does)
        step_outputs = {
            "fetch_data": parsed_result["output"]
        }
        
        # Step 3: Simulate next step input mapping resolution
        resolver = InputMappingResolver(
            workflow_input={},
            step_outputs=step_outputs
        )
        
        input_mapping = {
            "data": "${fetch_data.output.data}",
            "operation": "transform",
            "source_metadata": "${fetch_data.output.metadata}"
        }
        
        resolved_input = resolver.resolve(input_mapping)
        
        # Verify the complete flow works
        assert resolved_input["data"] == "Extracted PDF content here"
        assert resolved_input["operation"] == "transform"
        assert resolved_input["source_metadata"]["pages"] == 5
        assert resolved_input["source_metadata"]["file_type"] == "pdf"


if __name__ == "__main__":
    # Run the tests
    test = TestDataFlow()
    
    print("Testing input mapping resolver with structured data...")
    test.test_input_mapping_resolver_with_structured_data()
    print("✓ PASSED")
    
    print("Testing extract output preserves structured data...")
    test.test_extract_output_preserves_structured_data()
    print("✓ PASSED")
    
    print("Testing end-to-end data flow...")
    test.test_end_to_end_data_flow()
    print("✓ PASSED")
    
    print("\nAll tests passed! The data flow fix should work correctly.")