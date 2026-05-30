from __future__ import annotations

import argparse
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

from .source_api import SourceApi
from .source_connection import ConnectionPolicy, SourceConnectionService
from .source_constants import default_sources
from .source_http import SourceHttpApp
from .source_result import utc_now
from .source_store import SourceStore


MAX_BODY_BYTES = 1_000_000


def build_default_app(
    allowed_roots: tuple[Path, ...] = (),
    clock: Callable[[], datetime] = utc_now,
) -> SourceHttpApp:
    store = SourceStore(default_sources())
    policy = ConnectionPolicy.with_roots(allowed_roots) if allowed_roots else ConnectionPolicy()
    service = SourceConnectionService(store, policy, clock)
    return SourceHttpApp(SourceApi(service, clock), clock=clock)


def make_handler(app: SourceHttpApp):
    class SourceRequestHandler(BaseHTTPRequestHandler):
        server_version = "DataSentinelSourceMock/0.1"

        def do_GET(self):
            self._send(app.handle("GET", self.path, dict(self.headers)))

        def do_POST(self):
            body = self._read_body()
            if isinstance(body, dict):
                self._send(body)
                return
            self._send(app.handle("POST", self.path, dict(self.headers), body))

        def _read_body(self):
            length_header = self.headers.get("Content-Length", "0")
            try:
                length = int(length_header)
            except ValueError:
                length = 0
            if length < 0:
                length = 0
            if length > MAX_BODY_BYTES:
                return {
                    "status": 413,
                    "contentType": "application/problem+json",
                    "headers": {
                        "X-Trace-Id": "trace_body_too_large",
                        "X-Contract-Version": "0.1.0",
                    },
                    "body": {
                        "type": "https://datasentinel.local/problems/http-413",
                        "title": "Request body too large",
                        "status": 413,
                        "detail": "Request body exceeds the source connection mock limit.",
                        "instance": self.path,
                        "traceId": "trace_body_too_large",
                    },
                }
            return self.rfile.read(length) if length else b""

        def _send(self, response: dict):
            body = json.dumps(response["body"]).encode("utf-8")
            self.send_response(response["status"])
            self.send_header("Content-Type", response["contentType"])
            self.send_header("Content-Length", str(len(body)))
            for key, value in response["headers"].items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            return

    return SourceRequestHandler


def run(host: str = "127.0.0.1", port: int = 8000):
    app = build_default_app()
    server = ThreadingHTTPServer((host, port), make_handler(app))
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Run the DataSentinel source connection mock server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
