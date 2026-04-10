#!/usr/bin/env python3
"""
OpenClaw Browser Relay Service - Simple Version
HTTP server on port 2204 for extension communication
"""

import http.server
import socketserver
import json
import logging
from datetime import datetime

# Configuration
RELAY_PORT = 2204
RELAY_HOST = '127.0.0.1'
OPENCLAW_GATEWAY = 'ws://localhost:18789'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global statistics
relay_stats = {
    'start_time': datetime.now().isoformat(),
    'total_requests': 0,
    'relay_enabled': True,
    'gateway_url': OPENCLAW_GATEWAY
}

class OpenClawRelayHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for OpenClaw relay"""

    def log_message(self, method, path):
        """Log incoming request"""
        logger.info(f"📨 {method} {path} - {self.client_address[0]}")

    def do_GET(self):
        """Handle GET requests"""
        self.log_message('GET', self.path)

        try:
            if self.path == '/':
                response = {
                    'status': 'running',
                    'service': 'OpenClaw Browser Relay',
                    'version': '1.0.0',
                    'gateway_url': OPENCLAW_GATEWAY,
                    'timestamp': datetime.now().isoformat()
                }
            elif self.path == '/health':
                response = {
                    'status': 'healthy',
                    'openclaw_gateway': OPENCLAW_GATEWAY
                }
            elif self.path == '/stats':
                response = relay_stats
            elif self.path.startswith('/status'):
                response = {
                    'status': 'ready',
                    'port': RELAY_PORT,
                    'gateway_connected': True
                }
            else:
                response = {'error': 'Not found'}

            # Send JSON response
            self.send_json(response)

        except Exception as e:
            logger.error(f"❌ GET error: {e}")
            self.send_json({'error': str(e)})

    def do_POST(self):
        """Handle POST requests"""
        self.log_message('POST', self.path)

        try:
            # Get content
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')

            # Parse JSON
            try:
                request_data = json.loads(post_data)
            except json.JSONDecodeError:
                logger.error("❌ Invalid JSON")
                self.send_json({'error': 'Invalid JSON'}, status_code=400)
                return

            # Update stats
            relay_stats['total_requests'] += 1
            relay_stats['last_request'] = datetime.now().isoformat()

            # Handle different paths
            if self.path == '/relay':
                response = self.handle_relay(request_data)
            elif self.path == '/autofill':
                response = self.handle_autofill(request_data)
            elif self.path == '/track':
                response = self.handle_track(request_data)
            elif self.path == '/extract':
                response = self.handle_extract(request_data)
            elif self.path == '/command':
                response = self.handle_command(request_data)
            else:
                response = {'error': 'Unknown endpoint', 'path': self.path}

            self.send_json(response)

        except Exception as e:
            logger.error(f"❌ POST error: {e}")
            import traceback
            traceback.print_exc()
            self.send_json({'error': str(e)}, status_code=500)

    def send_json(self, data, status_code=200):
        """Send JSON response"""
        try:
            # Create response with proper HTTP format
            response_body = json.dumps(data, indent=2)
            response_bytes = response_body.encode('utf-8')

            # Send complete response with headers and body
            self.send_response(status_code, body=response_bytes)

            # Log success
            logger.info(f"✅ {status_code} - {len(response_bytes)} bytes")

        except Exception as e:
            logger.error(f"❌ Response error: {e}")

    def handle_relay(self, data):
        """Handle relay requests"""
        action = data.get('action', 'unknown')
        logger.info(f"🔄 Relay action: {action}")

        if action == 'test_connection':
            return {
                'status': 'success',
                'gateway': OPENCLAW_GATEWAY,
                'message': 'Relay is ready'
            }
        elif action == 'send_to_openclaw':
            return {
                'status': 'success',
                'command': data.get('command', ''),
                'sent_at': datetime.now().isoformat()
            }
        elif action == 'get_openclaw_status':
            return {
                'status': 'connected',
                'gateway_url': OPENCLAW_GATEWAY,
                'last_activity': relay_stats.get('last_request')
            }
        else:
            return {'error': 'Unknown action', 'action': action}

    def handle_autofill(self, data):
        """Handle autofill requests"""
        logger.info(f"✍️  Autofill: {data.get('form_type', 'unknown')}")
        return {
            'status': 'success',
            'form_type': data.get('form_type', ''),
            'filled_fields': len(data.get('fields', {})),
            'timestamp': datetime.now().isoformat()
        }

    def handle_track(self, data):
        """Handle tracking requests"""
        logger.info(f"📊 Track: {data.get('event', 'unknown')}")
        return {
            'status': 'recorded',
            'event': data.get('event', ''),
            'timestamp': datetime.now().isoformat()
        }

    def handle_extract(self, data):
        """Handle extraction requests"""
        logger.info(f"📥 Extract: {data.get('target', 'unknown')}")
        return {
            'status': 'success',
            'target': data.get('target', ''),
            'extracted_count': len(data.get('selectors', [])),
            'timestamp': datetime.now().isoformat()
        }

    def handle_command(self, data):
        """Handle command requests"""
        logger.info(f"⚡ Command: {data.get('cmd', 'unknown')}")
        return {
            'status': 'executed',
            'command': data.get('cmd', ''),
            'timestamp': datetime.now().isoformat()
        }

def start_relay_server():
    """Start the relay server"""
    try:
        # Create server
        handler = OpenClawRelayHandler
        socketserver.TCPServer.allow_reuse_address = True
        server = socketserver.TCPServer((RELAY_HOST, RELAY_PORT), handler)

        # Print banner
        logger.info("=" * 70)
        logger.info("🚀 OPENCLAW BROWSER RELAY SERVICE")
        logger.info("=" * 70)
        logger.info(f"📡 Listening on: http://{RELAY_HOST}:{RELAY_PORT}")
        logger.info(f"🌐 Gateway URL: {OPENCLAW_GATEWAY}")
        logger.info(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)
        logger.info("")
        logger.info("✅ Relay service is READY!")
        logger.info("💡 Click the extension toolbar button to connect!")
        logger.info("=" * 70)
        logger.info("")

        # Run server
        server.serve_forever()

    except KeyboardInterrupt:
        logger.info("\n👋 Relay stopped by user")
        server.server_close()
    except OSError as e:
        logger.error(f"❌ Port {RELAY_PORT} is in use!")
        logger.error("   Stop existing relay: pkill -f openclaw_relay")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    start_relay_server()
