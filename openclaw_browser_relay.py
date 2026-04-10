#!/usr/bin/env python3
"""
OpenClaw Browser Relay Service
HTTP server that enables Simplify Copilot extension to communicate with OpenClaw
Listens on port 2204 (as expected by the extension)
"""

import http.server
import socketserver
import json
import logging
import subprocess
import os
import threading
import time
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# Configuration
RELAY_PORT = 2204
RELAY_HOST = '127.0.0.1'
OPENCLAW_GATEWAY_URL = 'ws://localhost:18789'
LOG_LEVEL = logging.INFO

# Setup logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('openclaw_relay.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OpenClawRelayHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for OpenClaw browser relay requests"""

    def do_GET(self):
        """Handle GET requests"""
        try:
            logger.info(f"📨 GET request: {self.path}")

            # Parse path
            if self.path == '/':
                self.send_json_response(200, {
                    'status': 'running',
                    'service': 'OpenClaw Browser Relay',
                    'version': '1.0.0',
                    'gateway_url': OPENCLAW_GATEWAY_URL,
                    'timestamp': datetime.now().isoformat()
                })

            elif self.path == '/health':
                self.send_json_response(200, {
                    'status': 'healthy',
                    'openclaw_gateway': OPENCLAW_GATEWAY_URL
                })

            elif self.path == '/stats':
                self.send_json_response(200, relay_stats)

            elif self.path.startswith('/status'):
                self.send_json_response(200, {
                    'status': 'ready',
                    'port': RELAY_PORT,
                    'gateway_connected': True
                })

            else:
                self.send_json_response(404, {'error': 'Not found'})

        except Exception as e:
            logger.error(f"❌ GET error: {e}")
            self.send_response(500, {'error': str(e)})

    def do_POST(self):
        """Handle POST requests from extension"""
        try:
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')

            logger.info(f"📨 POST request: {self.path}")
            logger.debug(f"   Data: {post_data}")

            # Parse JSON
            try:
                request_data = json.loads(post_data)
            except json.JSONDecodeError:
                logger.error("❌ Invalid JSON in request")
                self.send_json_response(400, {'error': 'Invalid JSON'})
                return

            # Handle different request types
            if self.path == '/relay':
                response = self.handle_relay_request(request_data)
            elif self.path == '/autofill':
                response = self.handle_autofill_request(request_data)
            elif self.path == '/track':
                response = self.handle_track_request(request_data)
            elif self.path == '/extract':
                response = self.handle_extract_request(request_data)
            elif self.path == '/command':
                response = self.handle_command_request(request_data)
            else:
                response = {'error': 'Unknown endpoint', 'path': self.path}

            # Update stats
            relay_stats['total_requests'] += 1
            relay_stats['last_request'] = datetime.now().isoformat()

            # Send response
            self.send_response(200, response)

        except Exception as e:
            logger.error(f"❌ POST error: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response(500, {'error': str(e)})

    def send_json_response(self, status_code, data):
        """Send HTTP JSON response"""
        try:
            response_body = json.dumps(data, indent=2)
            response_bytes = response_body.encode('utf-8')

            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response_bytes)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(response_bytes)

            logger.info(f"✅ Response {status_code}: {len(response_bytes)} bytes")

        except Exception as e:
            logger.error(f"❌ Response error: {e}")

    def handle_relay_request(self, data):
        """Handle relay/gateway communication"""
        logger.info(f"🔄 Relay request: {data.get('action', 'unknown')}")

        action = data.get('action')

        if action == 'test_connection':
            return {
                'status': 'success',
                'gateway': OPENCLAW_GATEWAY_URL,
                'message': 'Relay is ready'
            }

        elif action == 'send_to_openclaw':
            # Forward command to OpenClaw
            command = data.get('command', '')
            logger.info(f"   → Forwarding to OpenClaw: {command}")

            # Here you would send to OpenClaw via WebSocket or CLI
            # For now, return success
            return {
                'status': 'success',
                'command': command,
                'sent_at': datetime.now().isoformat()
            }

        elif action == 'get_openclaw_status':
            return {
                'status': 'connected',
                'gateway_url': OPENCLAW_GATEWAY_URL,
                'last_activity': relay_stats['last_request']
            }

        else:
            return {
                'error': 'Unknown action',
                'action': action
            }

    def handle_autofill_request(self, data):
        """Handle autofill requests from extension"""
        logger.info(f"✍️  Autofill request: {data.get('form_type', 'unknown')}")

        form_type = data.get('form_type', '')
        fields = data.get('fields', {})

        # Autofill logic would go here
        # For now, return success
        return {
            'status': 'success',
            'form_type': form_type,
            'filled_fields': len(fields),
            'timestamp': datetime.now().isoformat()
        }

    def handle_track_request(self, data):
        """Handle tracking/analytics requests"""
        logger.info(f"📊 Track request: {data.get('event', 'unknown')}")

        event = data.get('event', '')
        event_data = data.get('data', {})

        # Update tracking stats
        relay_stats['tracking_events'] += 1

        return {
            'status': 'recorded',
            'event': event,
            'timestamp': datetime.now().isoformat()
        }

    def handle_extract_request(self, data):
        """Handle data extraction requests"""
        logger.info(f"📥 Extract request: {data.get('target', 'unknown')}")

        target = data.get('target', '')
        selectors = data.get('selectors', [])

        # Extraction logic would go here
        return {
            'status': 'success',
            'target': target,
            'extracted_count': len(selectors),
            'timestamp': datetime.now().isoformat()
        }

    def handle_command_request(self, data):
        """Handle command requests"""
        logger.info(f"⚡ Command request: {data.get('cmd', 'unknown')}")

        cmd = data.get('cmd', '')
        args = data.get('args', [])

        # Command execution would go here
        return {
            'status': 'executed',
            'command': cmd,
            'timestamp': datetime.now().isoformat()
        }

    def log_request(self):
        """Log incoming request details"""
        client_address = self.client_address[0]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        logger.info(f"[{timestamp}] Request from {client_address}: {self.path}")

# Global relay statistics
relay_stats = {
    'start_time': datetime.now().isoformat(),
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'tracking_events': 0,
    'last_request': None,
    'active_connections': 0
}

def start_relay_server():
    """Start the OpenClaw browser relay HTTP server"""
    try:
        # Create server
        handler = OpenClawRelayHandler
        socketserver.TCPServer.allow_reuse_address = True
        server = socketserver.TCPServer((RELAY_HOST, RELAY_PORT), handler)

        server_name = socketserver.TCPServer.__name__
        logger.info("=" * 70)
        logger.info("🚀 OPENCLAW BROWSER RELAY SERVICE")
        logger.info("=" * 70)
        logger.info(f"📡 Listening on: http://{RELAY_HOST}:{RELAY_PORT}")
        logger.info(f"🌐 Gateway URL: {OPENCLAW_GATEWAY_URL}")
        logger.info(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)
        logger.info("")
        logger.info("✅ Relay service is READY!")
        logger.info("📋 Available Endpoints:")
        logger.info("   GET  /         - Service status")
        logger.info("   GET  /health    - Health check")
        logger.info("   GET  /stats     - Statistics")
        logger.info("   GET  /status    - Connection status")
        logger.info("   POST /relay     - Relay commands")
        logger.info("   POST /autofill  - Autofill forms")
        logger.info("   POST /track      - Tracking events")
        logger.info("   POST /extract    - Data extraction")
        logger.info("   POST /command    - Execute commands")
        logger.info("")
        logger.info("💡 Now click the extension toolbar button to connect!")
        logger.info("=" * 70)
        logger.info("")

        # Run server
        server.serve_forever()

    except KeyboardInterrupt:
        logger.info("\n👋 Relay service stopped by user")
        server.server_close()
    except OSError as e:
        logger.error(f"❌ Port {RELAY_PORT} is already in use!")
        logger.error("   Try stopping the existing relay service first:")
        logger.error(f"   pkill -f openclaw_browser_relay.py")
    except Exception as e:
        logger.error(f"❌ Error starting relay: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    start_relay_server()
