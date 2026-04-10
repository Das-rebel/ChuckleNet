#!/usr/bin/env python3
"""
Simple HTTP Relay for OpenClaw Extension
Start with: python3 start_relay.py
"""

import http.server
import socketserver
import json
from datetime import datetime

PORT = 2204

class RelayHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse path
        path = self.path if self.path.endswith('/') else self.path

        # Create response
        if path == '/health':
            data = {'status': 'healthy', 'openclaw_gateway': 'ws://localhost:18789'}
        elif path == '/stats':
            data = {'status': 'running', 'port': PORT}
        elif path == '/status':
            data = {'status': 'ready', 'connected': True}
        elif path == '/':
            data = {'status': 'running', 'service': 'OpenClaw Relay', 'port': PORT}
        else:
            data = {'error': 'Not found'}

        # Send response
        response = json.dumps(data).encode('utf-8')
        self.send_response(200, 'application/json', len(response), response)

    def do_POST(self):
        # Get content
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')

        try:
            data = json.loads(post_data)
        except:
            data = {'error': 'Invalid JSON'}

        # Send response
        response = json.dumps({'status': 'success', 'received': data}).encode('utf-8')
        self.send_response(200, 'application/json', len(response), response)

    def send_response(self, code, content_type, length, body):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(length))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

if __name__ == '__main__':
    with socketserver.TCPServer(('', PORT), RelayHandler) as httpd:
        print(f"\n{'='*70}")
        print("🚀 OPENCLAW BROWSER RELAY")
        print(f"{'='*70}")
        print(f"\n📡 Listening on: http://127.0.0.1:{PORT}")
        print(f"✅ Ready! Extension should connect now.")
        print(f"{'='*70}\n")
        httpd.serve_forever()
