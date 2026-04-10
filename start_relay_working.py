#!/usr/bin/env python3
"""
OpenClaw Relay Server - Working Version
Simple HTTP server on port 2204
"""

import http.server
import socketserver
import json
from datetime import datetime

PORT = 2204

class RelayHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP request handler"""

    def do_GET(self):
        """Handle GET requests"""
        if self.path in ['/', '']:
            response_data = {
                'status': 'running',
                'service': 'OpenClaw Browser Relay',
                'version': '1.0.0',
                'gateway': 'ws://localhost:18789',
                'timestamp': datetime.now().isoformat()
            }
        elif self.path == '/health':
            response_data = {'status': 'healthy', 'openclaw_gateway': 'ws://localhost:18789'}
        elif self.path == '/stats':
            response_data = {'status': 'running', 'port': PORT}
        elif self.path.startswith('/status'):
            response_data = {'status': 'ready', 'connected': True, 'port': PORT}
        else:
            response_data = {'error': 'Not found'}

        # Send HTTP response
        response_body = json.dumps(response_data).encode('utf-8')
        self.send_response(200, 'application/json', len(response_body), response_body)

    def do_POST(self):
        """Handle POST requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            if self.path == '/relay':
                response_data = {'status': 'success', 'received': data}
            else:
                response_data = {'error': 'Unknown endpoint'}

            response_body = json.dumps(response_data).encode('utf-8')
            self.send_response(200, 'application/json', len(response_body), response_body)

        except json.JSONDecodeError:
            response_data = {'error': 'Invalid JSON'}
            response_body = json.dumps(response_data).encode('utf-8')
            self.send_response(400, 'application/json', len(response_body), response_body)

def main():
    try:
        with socketserver.TCPServer(('', PORT), RelayHandler) as httpd:
            print(f"\n{'='*70}")
            print("🚀 OPENCLAW RELAY SERVICE")
            print(f"{'='*70}")
            print(f"📡 Listening on: http://127.0.0.1:{PORT}")
            print(f"🌐 Gateway URL: ws://localhost:18789")
            print(f"{'='*70}")
            print("\n✅ READY!")
            print("💡 Click extension toolbar button to connect!")
            print(f"{'='*70}\n")

            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Relay stopped")
        httpd.server_close()
    except OSError as e:
        print(f"❌ Port {PORT} is in use!")
        print(f"   Stop: pkill -f python3 start_relay")

if __name__ == '__main__':
    main()
