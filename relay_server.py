#!/usr/bin/env python3
"""
OpenClaw Relay Server - Simple HTTP server
Listens on port 2204 for extension communication
"""

import http.server
import socketserver
import json
from datetime import datetime

PORT = 2204

class RelayHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP request handler"""

    def send_response(self, response_dict):
        """Send JSON response"""
        # Create JSON body
        response_body = json.dumps(response_dict).encode('utf-8')
        response_str = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {len(response_body)}\r\n\r\n{response_body.decode('utf-8')}"

        self.wfile.write(response_str.encode('utf-8'))
        print(f"✅ Sent response to {self.client_address[0]}")

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/' or self.path == '':
            self.send_response({
                'status': 'running',
                'service': 'OpenClaw Browser Relay',
                'version': '1.0.0',
                'gateway': 'ws://localhost:18789',
                'timestamp': datetime.now().isoformat()
            })
        elif self.path == '/health':
            self.send_response({'status': 'healthy', 'openclaw_gateway': 'ws://localhost:18789'})
        elif self.path == '/stats':
            self.send_response({'status': 'running', 'port': PORT})
        elif self.path.startswith('/status'):
            self.send_response({'status': 'ready', 'connected': True, 'port': PORT})
        else:
            self.send_response({'error': 'Not found'}, status_code=404)

    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')

        try:
            data = json.loads(post_data)
            print(f"📨 POST to {self.path}: {data}")

            if self.path == '/relay':
                self.send_response({'status': 'success', 'received': data})
            else:
                self.send_response({'error': 'Unknown endpoint'})
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON: {post_data}")
            self.send_response({'error': 'Invalid JSON'}, status_code=400)

def main():
    try:
        with socketserver.TCPServer(('', PORT), RelayHandler) as httpd:
            print(f"\n{'='*70}")
            print("🚀 OPENCLAW RELAY SERVICE")
            print(f"{'='*70}")
            print(f"📡 Listening on: http://127.0.0.1:{PORT}")
            print(f"🌐 OpenClaw Gateway: ws://localhost:18789")
            print(f"{'='*70}")
            print("\n✅ READY!")
            print(f"{'='*70}")
            print("💡 Click extension toolbar button to connect!")
            print(f"{'='*70}\n")

            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Relay stopped")
    except OSError as e:
        print(f"❌ Port {PORT} already in use!")
        print(f"   Stop: pkill -f python3 start_relay.py")

if __name__ == '__main__':
    main()
