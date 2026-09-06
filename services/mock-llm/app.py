"""Deterministic OpenAI-compatible mock chat-completions server.

Stands in for a real LLM provider so the gateway, guardrails, and e2e tests
have something to route to without any network dependency or API key.
"""

import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8080
MODEL_NAME = "mock-llm"
CANNED_REPLY = "This is a deterministic response from the mock LLM backend."


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/healthz":
            self._send_json(200, {"status": "ok"})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self._send_json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            request = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": {"message": "invalid JSON body"}})
            return

        model = request.get("model", MODEL_NAME)
        messages = request.get("messages", [])
        prompt_tokens = sum(len(m.get("content", "").split()) for m in messages)
        completion_tokens = len(CANNED_REPLY.split())

        self._send_json(
            200,
            {
                "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": CANNED_REPLY},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
            },
        )

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}")


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"mock-llm listening on :{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
