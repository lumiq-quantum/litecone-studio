#!/usr/bin/env python3
"""
Mock A2A Agent for Testing

A simple HTTP server that simulates an A2A-compliant agent for testing purposes.
Supports both Simple A2A and JSON-RPC 2.0 protocols.
Supports configurable delays and error modes via environment variables.
"""

import json
import os
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment
AGENT_NAME = os.getenv('AGENT_NAME', 'MockAgent')
PORT = int(os.getenv('AGENT_PORT', '8080'))
DELAY_MS = int(os.getenv('AGENT_DELAY_MS', '0'))
ERROR_MODE = os.getenv('AGENT_ERROR_MODE', 'none')  # none, timeout, 4xx, 5xx, jsonrpc_error
ERROR_RATE = float(os.getenv('AGENT_ERROR_RATE', '0.0'))  # 0.0 to 1.0
PROTOCOL = os.getenv('AGENT_PROTOCOL', 'jsonrpc-2.0')  # simple-a2a or jsonrpc-2.0


class MockAgentHandler(BaseHTTPRequestHandler):
    """HTTP request handler for mock A2A agent"""
    
    def log_message(self, format, *args):
        """Override to use logger instead of stderr"""
        logger.info(f"{self.address_string()} - {format % args}")
    
    def do_POST(self):
        """Handle POST requests (A2A agent invocation)"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            request_data = json.loads(body.decode('utf-8'))
            
            logger.info(f"Received request: {json.dumps(request_data, indent=2)}")
            
            # Detect protocol and process accordingly
            if self._is_jsonrpc_request(request_data):
                self._handle_jsonrpc_request(request_data)
            else:
                self._handle_simple_a2a_request(request_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in request: {e}")
            self._send_error_response('unknown', f"Invalid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            self._send_error_response('unknown', str(e))
    
    def _is_jsonrpc_request(self, request_data: Dict[str, Any]) -> bool:
        """Check if request is JSON-RPC 2.0 format"""
        return 'jsonrpc' in request_data
    
    def _handle_simple_a2a_request(self, request_data: Dict[str, Any]):
        """Handle Simple A2A protocol request"""
        # Extract task details
        task_id = request_data.get('task_id', 'unknown')
        input_data = request_data.get('input', {})
        
        # Simulate processing delay
        if DELAY_MS > 0:
            logger.info(f"Simulating {DELAY_MS}ms delay")
            time.sleep(DELAY_MS / 1000.0)
        
        # Check if we should simulate an error
        import random
        if ERROR_MODE != 'none' and random.random() < ERROR_RATE:
            self._send_error_response(task_id)
            return
        
        # Generate mock response based on agent name
        output_data = self._generate_mock_output(input_data)
        
        # Send A2A-compliant response
        response = {
            'task_id': task_id,
            'status': 'success',
            'output': output_data,
            'error': None
        }
        
        logger.info(f"Sending Simple A2A response: {json.dumps(response, indent=2)}")
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _handle_jsonrpc_request(self, request_data: Dict[str, Any]):
        """Handle JSON-RPC 2.0 protocol request"""
        # Validate JSON-RPC request structure
        validation_error = self._validate_jsonrpc_request(request_data)
        if validation_error:
            self._send_jsonrpc_error_response(
                request_data.get('id'),
                -32600,
                validation_error
            )
            return
        
        request_id = request_data.get('id')
        method = request_data.get('method')
        params = request_data.get('params', {})
        
        logger.info(f"Processing JSON-RPC method: {method}")
        
        # Simulate processing delay
        if DELAY_MS > 0:
            logger.info(f"Simulating {DELAY_MS}ms delay")
            time.sleep(DELAY_MS / 1000.0)
        
        # Check if we should simulate an error
        import random
        if ERROR_MODE == 'jsonrpc_error' and random.random() < ERROR_RATE:
            self._send_jsonrpc_error_response(
                request_id,
                -32000,
                "Simulated JSON-RPC error"
            )
            return
        elif ERROR_MODE != 'none' and ERROR_MODE != 'jsonrpc_error' and random.random() < ERROR_RATE:
            self._send_error_response(request_id)
            return
        
        # Extract input from message parts
        input_data = self._extract_input_from_message(params)
        
        # Generate mock output
        output_data = self._generate_mock_output(input_data)
        
        # Build JSON-RPC response with artifacts and history
        response = self._build_jsonrpc_response(request_id, output_data, params)
        
        logger.info(f"Sending JSON-RPC response: {json.dumps(response, indent=2)}")
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _validate_jsonrpc_request(self, request_data: Dict[str, Any]) -> Optional[str]:
        """Validate JSON-RPC 2.0 request structure. Returns error message if invalid."""
        # Check required fields
        if 'jsonrpc' not in request_data:
            return "Missing 'jsonrpc' field"
        
        if request_data['jsonrpc'] != '2.0':
            return f"Invalid JSON-RPC version: {request_data['jsonrpc']}"
        
        if 'method' not in request_data:
            return "Missing 'method' field"
        
        if 'id' not in request_data:
            return "Missing 'id' field"
        
        # Validate method
        method = request_data['method']
        if method != 'message/send':
            return f"Unsupported method: {method}"
        
        # Validate params structure
        params = request_data.get('params', {})
        if not isinstance(params, dict):
            return "'params' must be an object"
        
        if 'message' not in params:
            return "Missing 'message' in params"
        
        message = params['message']
        if not isinstance(message, dict):
            return "'message' must be an object"
        
        # Validate message structure
        if 'role' not in message:
            return "Missing 'role' in message"
        
        if 'parts' not in message:
            return "Missing 'parts' in message"
        
        if not isinstance(message['parts'], list):
            return "'parts' must be an array"
        
        return None
    
    def _extract_input_from_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract input data from JSON-RPC message parts"""
        message = params.get('message', {})
        parts = message.get('parts', [])
        
        # Combine all text parts
        text_parts = []
        for part in parts:
            if part.get('kind') == 'text':
                text_parts.append(part.get('text', ''))
        
        combined_text = '\n'.join(text_parts)
        
        # Try to parse as JSON, otherwise return as text
        try:
            return json.loads(combined_text)
        except json.JSONDecodeError:
            return {'text': combined_text}
    
    def _build_jsonrpc_response(
        self,
        request_id: str,
        output_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build JSON-RPC 2.0 response with artifacts and history"""
        # Generate response text
        if isinstance(output_data, dict):
            response_text = json.dumps(output_data, indent=2)
        else:
            response_text = str(output_data)
        
        # Build artifacts
        artifacts = [
            {
                'kind': 'result',
                'parts': [
                    {
                        'kind': 'text',
                        'text': response_text
                    }
                ],
                'metadata': {
                    'agent_name': AGENT_NAME,
                    'timestamp': time.time()
                }
            }
        ]
        
        # Build history with user message and agent response
        message_id = params.get('message', {}).get('messageId', str(uuid.uuid4()))
        history = [
            {
                'role': 'user',
                'messageId': message_id,
                'parts': params.get('message', {}).get('parts', [])
            },
            {
                'role': 'agent',
                'messageId': f"agent-{message_id}",
                'parts': [
                    {
                        'kind': 'text',
                        'text': response_text
                    }
                ]
            }
        ]
        
        # Build result
        result = {
            'status': {
                'state': 'completed',
                'message': 'Task completed successfully'
            },
            'artifacts': artifacts,
            'history': history,
            'metadata': {
                'agent_name': AGENT_NAME,
                'processing_time_ms': DELAY_MS
            }
        }
        
        # Build JSON-RPC response
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': result
        }
    
    def _send_jsonrpc_error_response(
        self,
        request_id: Optional[str],
        error_code: int,
        error_message: str
    ):
        """Send JSON-RPC 2.0 error response"""
        response = {
            'jsonrpc': '2.0',
            'id': request_id,
            'error': {
                'code': error_code,
                'message': error_message
            }
        }
        
        logger.warning(f"Sending JSON-RPC error response: {json.dumps(response, indent=2)}")
        
        self.send_response(200)  # JSON-RPC errors use 200 status
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _send_error_response(self, task_id: str, error_msg: str = None):
        """Send an error response based on ERROR_MODE"""
        if ERROR_MODE == '4xx':
            status_code = 400
            error_message = error_msg or "Bad request - invalid input format"
        elif ERROR_MODE == '5xx':
            status_code = 500
            error_message = error_msg or "Internal server error"
        elif ERROR_MODE == 'timeout':
            # Simulate timeout by sleeping longer than expected
            logger.info("Simulating timeout - sleeping for 60 seconds")
            time.sleep(60)
            return
        else:
            status_code = 500
            error_message = error_msg or "Unknown error"
        
        response = {
            'task_id': task_id,
            'status': 'error',
            'output': None,
            'error': error_message
        }
        
        logger.warning(f"Sending error response ({status_code}): {error_message}")
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _generate_mock_output(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock output based on agent name and input"""
        if AGENT_NAME == 'ResearchAgent':
            return {
                'findings': [
                    {
                        'source': 'Mock Source 1',
                        'content': f"Research finding about {input_data.get('topic', 'unknown topic')}"
                    },
                    {
                        'source': 'Mock Source 2',
                        'content': f"Additional research on {input_data.get('topic', 'unknown topic')}"
                    }
                ],
                'summary': f"Summary of research on {input_data.get('topic', 'unknown topic')}",
                'confidence': 0.85,
                'sources_count': 2
            }
        elif AGENT_NAME == 'WriterAgent':
            research_data = input_data.get('research_data', [])
            style = input_data.get('style', 'formal')
            return {
                'article': f"This is a {style} article based on {len(research_data)} research findings.",
                'word_count': input_data.get('word_count', 500),
                'style': style,
                'quality_score': 0.92
            }
        else:
            # Generic response
            return {
                'result': f"Processed by {AGENT_NAME}",
                'input_received': input_data,
                'timestamp': time.time()
            }
    
    def do_GET(self):
        """Handle GET requests (health check)"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'agent_name': AGENT_NAME,
                'protocol': PROTOCOL,
                'supported_protocols': ['simple-a2a', 'jsonrpc-2.0'],
                'error_mode': ERROR_MODE
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()


def run_server():
    """Start the mock agent HTTP server"""
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, MockAgentHandler)
    
    logger.info(f"Starting {AGENT_NAME} on port {PORT}")
    logger.info(f"Protocol: {PROTOCOL}")
    logger.info(f"Configuration: delay={DELAY_MS}ms, error_mode={ERROR_MODE}, error_rate={ERROR_RATE}")
    logger.info(f"Health check available at http://localhost:{PORT}/health")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server")
        httpd.shutdown()


if __name__ == '__main__':
    run_server()
