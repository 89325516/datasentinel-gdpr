from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from backend.datasentinel import (
    ConnectionPolicy,
    SourceApi,
    SourceConnectionService,
    SourceHttpApp,
    SourceStore,
    default_sources,
)


def fixed_clock() -> datetime:
    return datetime(2026, 5, 30, 12, 0, tzinfo=UTC)


def app_for(sources=None, policy=None) -> SourceHttpApp:
    store = SourceStore(sources or default_sources())
    service = SourceConnectionService(store, policy or ConnectionPolicy(), fixed_clock)
    api = SourceApi(service, fixed_clock)
    return SourceHttpApp(api, lambda: "trace_http_test", fixed_clock)


class SourceHttpTests(unittest.TestCase):
    def test_health_route_returns_contract_envelope(self):
        response = app_for().handle("GET", "/api/health")

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["contentType"], "application/json")
        self.assertEqual(response["headers"]["X-Trace-Id"], "trace_http_test")
        self.assertEqual(response["body"]["data"]["status"], "ok")
        self.assertEqual(response["body"]["meta"]["contractVersion"], "0.1.0")

    def test_list_sources_route_returns_seed_sources(self):
        response = app_for().handle("GET", "/api/sources", {"X-Trace-Id": "trace_client"})

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["headers"]["X-Trace-Id"], "trace_client")
        self.assertGreaterEqual(len(response["body"]["data"]), 2)
        self.assertEqual(response["body"]["data"][0]["sourceId"], "source_001")

    def test_create_source_then_connect_local_source(self):
        with tempfile.TemporaryDirectory() as root:
            sample_dir = Path(root) / "samples"
            sample_dir.mkdir()
            (sample_dir / "sample.pdf").write_bytes(b"%PDF-1.4")
            app = app_for(default_sources(), ConnectionPolicy.with_roots([Path(root)]))
            body = json.dumps(
                {
                    "sourceId": "source_local_http",
                    "name": "Local HTTP Samples",
                    "sourceType": "local_repo",
                    "config": {"rootPath": str(sample_dir)},
                }
            )

            created = app.handle("POST", "/api/sources", {"Content-Type": "application/json"}, body)
            connected = app.handle("POST", "/api/sources/source_local_http/connect-test")

            self.assertEqual(created["status"], 201)
            self.assertEqual(connected["status"], 200)
            self.assertTrue(connected["body"]["data"]["reachable"])
            self.assertEqual(connected["body"]["data"]["connectionStatus"], "connected")

    def test_empty_local_source_is_degraded(self):
        with tempfile.TemporaryDirectory() as root:
            empty_dir = Path(root) / "empty"
            empty_dir.mkdir()
            app = app_for(
                [
                    {
                        "sourceId": "source_empty",
                        "name": "Empty",
                        "sourceType": "local_repo",
                        "config": {"rootPath": str(empty_dir)},
                    }
                ],
                ConnectionPolicy.with_roots([Path(root)]),
            )

            response = app.handle("POST", "/api/sources/source_empty/connect-test")

            self.assertEqual(response["body"]["data"]["connectionStatus"], "degraded")
            self.assertTrue(response["body"]["meta"]["partial"])
            self.assertEqual(response["body"]["data"]["diagnostics"][0]["code"], "source.local_empty")

    def test_file_path_local_source_is_invalid_config(self):
        with tempfile.TemporaryDirectory() as root:
            file_path = Path(root) / "sample.pdf"
            file_path.write_bytes(b"%PDF-1.4")
            app = app_for(
                [
                    {
                        "sourceId": "source_file",
                        "name": "File",
                        "sourceType": "local_repo",
                        "config": {"rootPath": str(file_path)},
                    }
                ],
                ConnectionPolicy.with_roots([Path(root)]),
            )

            response = app.handle("POST", "/api/sources/source_file/connect-test")

            self.assertFalse(response["body"]["data"]["reachable"])
            self.assertEqual(response["body"]["data"]["connectionStatus"], "invalid_config")
            self.assertEqual(response["body"]["data"]["diagnostics"][0]["code"], "source.root_path_not_directory")

    def test_relative_local_path_is_invalid_config(self):
        response = app_for(
            [
                {
                    "sourceId": "source_relative",
                    "name": "Relative",
                    "sourceType": "local_repo",
                    "config": {"rootPath": "samples"},
                }
            ]
        ).handle("POST", "/api/sources/source_relative/connect-test")

        self.assertEqual(response["body"]["data"]["connectionStatus"], "invalid_config")
        self.assertEqual(response["body"]["data"]["diagnostics"][0]["code"], "source.root_path_relative")

    def test_post_sources_rejects_unsupported_media_type(self):
        response = app_for().handle("POST", "/api/sources", {"Content-Type": "text/plain"}, "{}")

        self.assertEqual(response["status"], 415)
        self.assertEqual(response["contentType"], "application/problem+json")

    def test_post_sources_rejects_malformed_json(self):
        response = app_for().handle("POST", "/api/sources", {"Content-Type": "application/json"}, "{")

        self.assertEqual(response["status"], 400)
        self.assertEqual(response["body"]["title"], "Malformed JSON")

    def test_post_sources_rejects_non_object_json(self):
        response = app_for().handle("POST", "/api/sources", {"Content-Type": "application/json"}, "[]")

        self.assertEqual(response["status"], 422)
        self.assertEqual(response["body"]["errors"][0]["pointer"], "#")

    def test_unknown_route_returns_problem_details(self):
        response = app_for().handle("GET", "/api/unknown")

        self.assertEqual(response["status"], 404)
        self.assertEqual(response["contentType"], "application/problem+json")
        self.assertEqual(response["body"]["instance"], "/api/unknown")

    def test_wrong_method_returns_problem_details(self):
        response = app_for().handle("DELETE", "/api/sources")

        self.assertEqual(response["status"], 405)
        self.assertEqual(response["contentType"], "application/problem+json")

    def test_unknown_source_subroute_returns_not_found(self):
        response = app_for().handle("GET", "/api/sources/source_001/unknown")

        self.assertEqual(response["status"], 404)
        self.assertEqual(response["contentType"], "application/problem+json")

    def test_empty_post_body_uses_validation_problem(self):
        response = app_for().handle("POST", "/api/sources", {"Content-Type": "application/json"}, "")

        self.assertEqual(response["status"], 422)
        self.assertEqual(response["body"]["errors"][0]["pointer"], "#/name")


if __name__ == "__main__":
    unittest.main()
