#!/usr/bin/env python3
"""Serve a key Nous (agents.nous) em 127.0.0.1:8999/key — com CORS para fetch de browser."""
import json, os, http.server, socketserver

auth = json.load(open(os.path.expanduser('~/.hermes/auth.json')))
key = (auth.get('providers', {}).get('nous', {}).get('agent_key') or '').strip()

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        self.wfile.write(key.encode())
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
    def log_message(self, *a):
        pass

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', 8999), H) as httpd:
    print('key server up on :8999 (len=%d, CORS ok)' % len(key), flush=True)
    httpd.serve_forever()
