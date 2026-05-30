from __future__ import annotations

import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer

from backend.datasentinel import build_default_app, make_handler


class SourceServerTests(unittest.TestCase):
    def with_server(self, callback):
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(build_default_app()))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            callback(server.server_address)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def request(self, address, method: str, path: str, body: str | None = None, headers=None):
        connection = http.client.HTTPConnection(address[0], address[1], timeout=5)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            payload = json.loads(response.read().decode("utf-8"))
            return response.status, response.getheaders(), payload
        finally:
            connection.close()

    def test_server_lists_sources_over_real_http(self):
        def check(address):
            status, headers, payload = self.request(address, "GET", "/api/sources")

            self.assertEqual(status, 200)
            self.assertEqual(dict(headers)["X-Contract-Version"], "0.1.0")
            self.assertGreaterEqual(len(payload["data"]), 2)

        self.with_server(check)

    def test_server_runs_connection_test_over_real_http(self):
        def check(address):
            status, headers, payload = self.request(address, "POST", "/api/sources/source_001/connect-test")

            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["connectionStatus"], "connected")
            self.assertEqual(dict(headers)["X-Contract-Version"], "0.1.0")

        self.with_server(check)

    def test_server_returns_problem_for_bad_json_over_real_http(self):
        def check(address):
            status, headers, payload = self.request(
                address,
                "POST",
                "/api/sources",
                body="{",
                headers={"Content-Type": "application/json"},
            )

            self.assertEqual(status, 400)
            self.assertEqual(dict(headers)["Content-Type"], "application/problem+json")
            self.assertEqual(payload["title"], "Malformed JSON")

        self.with_server(check)


if __name__ == "__main__":
    unittest.main()

