#!/usr/bin/env python3
"""
Mock A2A Agent for Testing

A simple HTTP server that simulates an A2A-compliant agent for testing purposes.
Supports configurable delays and error modes via environment variables.
"""

import json
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any
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
ERROR_MODE = os.getenv('AGENT_ERROR_MODE', 'none')  # none, timeout, 4xx, 5xx
ERROR_RATE = float(os.getenv('AGENT_ERROR_RATE', '0.0'))  # 0.0 to 1.0


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
            
            logger.info(f"Sending response: {json.dumps(response, indent=2)}")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            self._send_error_response('unknown', str(e))
    
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
    logger.info(f"Configuration: delay={DELAY_MS}ms, error_mode={ERROR_MODE}, error_rate={ERROR_RATE}")
    logger.info(f"Health check available at http://localhost:{PORT}/health")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server")
        httpd.shutdown()


if __name__ == '__main__':
    run_server()
