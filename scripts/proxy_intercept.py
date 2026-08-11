#!/usr/bin/env python3
"""Proxy de interceptação: loga request OpenAI e repassa para a Nous.

FIX 11/08: (1) User-Agent de browser obrigatório — sem ele o Cloudflare da Nous
responde 403 error code 1010; (2) sobrescreve Authorization com a key fresca do
auth.json (token OAuth expira ~1h e o Studio guarda key velha -> 401 Unauthorized).
"""
import json, os, http.server, socketserver, urllib.request, urllib.error, sys

UPSTREAM = "https://inference-api.nousresearch.com"
LOG_PATH = "/tmp/proxy_log.jsonl"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def _fresh_key():
    try:
        auth = json.load(open(os.path.expanduser("~/.hermes/auth.json")))
        k = (auth.get("providers", {}).get("nous", {}).get("agent_key") or "").strip()
        return k
    except Exception:
        return ""

class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        # logar
        with open(LOG_PATH, 'a') as f:
            f.write(json.dumps({
                "path": self.path,
                "headers": dict(self.headers),
                "body": body.decode("utf-8", errors="replace")
            }) + "\n")
        # repassar (normaliza path: Studio chama /v1/chat/completions — não duplicar)
        path = self.path if self.path.startswith('/v1') else '/v1' + self.path
        url = UPSTREAM + path
        req = urllib.request.Request(url, data=body, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('User-Agent', UA)
        # key fresca do auth.json vence key velha do Studio (token OAuth expira ~1h)
        fresh = _fresh_key()
        if fresh:
            req.add_header('Authorization', 'Bearer ' + fresh)
        else:
            auth = self.headers.get('Authorization', '')
            if auth:
                req.add_header('Authorization', auth)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self.send_header('Content-Type', resp.headers.get('Content-Type', 'application/json'))
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            msg = json.dumps({"error": {"message": str(e)[:200]}}).encode()
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
    def log_message(self, *a):
        pass

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', 8998), H) as httpd:
    print("proxy up on :8998 -> nous", flush=True)
    httpd.serve_forever()
