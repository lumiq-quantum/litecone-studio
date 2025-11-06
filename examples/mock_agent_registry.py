#!/usr/bin/env python3
"""
Mock Agent Registry for Testing

A simple HTTP server that provides agent metadata for testing purposes.
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PORT = int(os.getenv('PORT', '8080'))

# Mock agent metadata
AGENTS = {
    "ResearchAgent": {
        "name": "ResearchAgent",
        "url": "http://research-agent:8080",
        "auth_config": None,
        "timeout": 30000,
        "retry_config": {
            "max_retries": 3,
            "initial_delay_ms": 100,
            "max_delay_ms": 5000,
            "backoff_multiplier": 2.0
        }
    },
    "WriterAgent": {
        "name": "WriterAgent",
        "url": "http://writer-agent:8080",
        "auth_config": None,
        "timeout": 30000,
        "retry_config": {
            "max_retries": 3,
            "initial_delay_ms": 100,
            "max_delay_ms": 5000,
            "backoff_multiplier": 2.0
        }
    }
}


class AgentRegistryHandler(BaseHTTPRequestHandler):
    """HTTP request handler for mock agent registry"""
    
    def log_message(self, format, *args):
        """Override to use logger instead of stderr"""
        logger.info(f"{self.address_string()} - {format % args}")
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self._send_json_response(200, {"status": "healthy"})
        elif self.path.startswith('/agents/'):
            # Extract agent name from path
            parts = self.path.split('/')
            if len(parts) >= 3:
                agent_name = parts[2]
                
                # Check for recovery endpoint
                if len(parts) == 4 and parts[3] == 'recovery':
                    self._send_json_response(200, {
                        "on_failure": "RETRY",
                        "fallback_agent": None,
                        "max_retries": 3
                    })
                else:
                    # Get agent metadata
                    if agent_name in AGENTS:
                        self._send_json_response(200, AGENTS[agent_name])
                    else:
                        self._send_json_response(404, {"error": "Agent not found"})
            else:
                self._send_json_response(404, {"error": "Invalid path"})
        else:
            self._send_json_response(404, {"error": "Not found"})
    
    def _send_json_response(self, status_code, data):
        """Send a JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))


def run_server():
    """Start the mock agent registry HTTP server"""
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, AgentRegistryHandler)
    
    logger.info(f"Starting Mock Agent Registry on port {PORT}")
    logger.info(f"Registered agents: {list(AGENTS.keys())}")
    logger.info(f"Health check available at http://localhost:{PORT}/health")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server")
        httpd.shutdown()


if __name__ == '__main__':
    run_server()
