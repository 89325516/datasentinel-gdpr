from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from backend.datasentinel import (
    ConnectionIssue,
    ConnectionPolicy,
    SourceApi,
    SourceConnectionService,
    SourceStore,
    default_sources,
    problem_from_issue,
)


def fixed_clock() -> datetime:
    return datetime(2026, 5, 30, 12, 0, tzinfo=UTC)


class SourceConnectionTests(unittest.TestCase):
    def service(self, sources=None, policy=None):
        store = SourceStore(sources or default_sources())
        return SourceConnectionService(store, policy or ConnectionPolicy(), fixed_clock)

    def source_api(self, sources=None, policy=None):
        store = SourceStore(sources or default_sources())
        service = SourceConnectionService(store, policy or ConnectionPolicy(), fixed_clock)
        return SourceApi(service, fixed_clock)

    def test_default_organizer_source_is_metadata_connected(self):
        envelope = self.service().connection_envelope("source_001", "trace_test")

        self.assertEqual(envelope["data"]["sourceId"], "source_001")
        self.assertTrue(envelope["data"]["reachable"])
        self.assertEqual(envelope["data"]["connectionStatus"], "connected")
        self.assertFalse(envelope["data"]["capabilities"]["canReadContent"])
        self.assertTrue(envelope["data"]["capabilities"]["canReadMetadata"])
        self.assertEqual(envelope["meta"]["contractVersion"], "0.1.0")
        self.assertFalse(envelope["meta"]["partial"])
        self.assertNotIn("download_url", str(envelope))

    def test_source_api_connection_response_matches_contract_headers(self):
        response = self.source_api().test_connection("source_001", "trace_api")

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["contentType"], "application/json")
        self.assertEqual(response["headers"]["X-Trace-Id"], "trace_api")
        self.assertEqual(response["headers"]["X-Contract-Version"], "0.1.0")
        self.assertEqual(response["body"]["data"]["connectionStatus"], "connected")

    def test_unsafe_organizer_url_is_rejected_without_remote_access(self):
        service = self.service(
            [
                {
                    "sourceId": "source_bad",
                    "name": "Unsafe",
                    "sourceType": "organizer_sample_repo",
                    "referenceUrl": "https://token@example.com/a-klumpp/GDPR-data-samples?ref=main",
                    "sampleFamilies": [],
                }
            ]
        )

        result = service.test_connection("source_bad")

        self.assertFalse(result["reachable"])
        self.assertEqual(result["connectionStatus"], "unsafe_reference")
        self.assertEqual(result["diagnostics"][0]["code"], "source.reference_credentials")
        self.assertNotIn("token", str(result))

    def test_missing_sample_family_returns_degraded_partial_result(self):
        service = self.service(
            [
                {
                    "sourceId": "source_degraded",
                    "name": "Partial",
                    "sourceType": "organizer_sample_repo",
                    "referenceUrl": "https://github.com/a-klumpp/GDPR-data-samples",
                    "sampleFamilies": ["Expense_Report"],
                }
            ]
        )

        envelope = service.connection_envelope("source_degraded", "trace_partial")

        self.assertTrue(envelope["data"]["reachable"])
        self.assertEqual(envelope["data"]["connectionStatus"], "degraded")
        self.assertTrue(envelope["meta"]["partial"])
        self.assertIn("Missing expected sample families", envelope["meta"]["warnings"][0])

    def test_unknown_source_returns_problem_details(self):
        service = self.service()

        with self.assertRaises(ConnectionIssue) as raised:
            service.test_connection("source_missing")

        problem = problem_from_issue(raised.exception, "/api/sources/source_missing/connect-test", "trace_404")

        self.assertEqual(problem["status"], 404)
        self.assertEqual(problem["traceId"], "trace_404")
        self.assertEqual(problem["errors"][0]["pointer"], "#/sourceId")

    def test_source_api_unknown_source_returns_problem_response(self):
        response = self.source_api().test_connection("source_missing", "trace_api_404")

        self.assertEqual(response["status"], 404)
        self.assertEqual(response["contentType"], "application/problem+json")
        self.assertEqual(response["body"]["traceId"], "trace_api_404")
        self.assertEqual(response["body"]["errors"][0]["pointer"], "#/sourceId")

    def test_unsupported_source_type_is_neutral_result(self):
        service = self.service(
            [
                {
                    "sourceId": "source_unknown",
                    "name": "Unknown",
                    "sourceType": "future_connector",
                    "status": "registered",
                }
            ]
        )

        result = service.test_connection("source_unknown")

        self.assertFalse(result["reachable"])
        self.assertEqual(result["connectionStatus"], "unsupported_type")
        self.assertEqual(result["diagnostics"][0]["severity"], "warning")

    def test_mock_sharepoint_source_does_not_claim_production_access(self):
        result = self.service().test_connection("source_002")

        self.assertTrue(result["reachable"])
        self.assertEqual(result["connectionStatus"], "connected")
        self.assertFalse(result["capabilities"]["canReadContent"])
        self.assertEqual(result["diagnostics"][0]["code"], "source.mock_only")

    def test_local_source_inside_allowed_root_connects(self):
        with tempfile.TemporaryDirectory() as root:
            source_dir = Path(root) / "samples"
            source_dir.mkdir()
            (source_dir / "sample.txt").write_text("metadata only", encoding="utf-8")
            service = self.service(
                [
                    {
                        "sourceId": "source_local",
                        "name": "Local",
                        "sourceType": "local_repo",
                        "config": {"rootPath": str(source_dir)},
                    }
                ],
                ConnectionPolicy.with_roots([Path(root)]),
            )

            result = service.test_connection("source_local")

            self.assertTrue(result["reachable"])
            self.assertEqual(result["connectionStatus"], "connected")
            self.assertTrue(result["capabilities"]["canReadContent"])

    def test_local_source_outside_allowed_root_is_denied(self):
        with tempfile.TemporaryDirectory() as allowed_root:
            with tempfile.TemporaryDirectory() as outside_root:
                service = self.service(
                    [
                        {
                            "sourceId": "source_local",
                            "name": "Local",
                            "sourceType": "local_repo",
                            "config": {"rootPath": outside_root},
                        }
                    ],
                    ConnectionPolicy.with_roots([Path(allowed_root)]),
                )

                result = service.test_connection("source_local")

                self.assertFalse(result["reachable"])
                self.assertEqual(result["connectionStatus"], "policy_denied")

    def test_local_symlink_escape_is_denied(self):
        with tempfile.TemporaryDirectory() as allowed_root:
            with tempfile.TemporaryDirectory() as outside_root:
                link = Path(allowed_root) / "link"
                link.symlink_to(outside_root)
                service = self.service(
                    [
                        {
                            "sourceId": "source_local",
                            "name": "Local",
                            "sourceType": "local_repo",
                            "config": {"rootPath": str(link)},
                        }
                    ],
                    ConnectionPolicy.with_roots([Path(allowed_root)]),
                )

                result = service.test_connection("source_local")

                self.assertFalse(result["reachable"])
                self.assertEqual(result["connectionStatus"], "policy_denied")

    def test_local_source_missing_path_is_retryable_not_found(self):
        with tempfile.TemporaryDirectory() as root:
            missing = Path(root) / "missing"
            service = self.service(
                [
                    {
                        "sourceId": "source_local",
                        "name": "Local",
                        "sourceType": "local_repo",
                        "config": {"rootPath": str(missing)},
                    }
                ],
                ConnectionPolicy.with_roots([Path(root)]),
            )

            result = service.test_connection("source_local")

            self.assertFalse(result["reachable"])
            self.assertEqual(result["connectionStatus"], "not_found")
            self.assertTrue(result["diagnostics"][0]["retryable"])

    def test_local_source_without_root_path_is_invalid_config(self):
        service = self.service(
            [
                {
                    "sourceId": "source_local",
                    "name": "Local",
                    "sourceType": "local_repo",
                    "config": {},
                }
            ]
        )

        result = service.test_connection("source_local")

        self.assertFalse(result["reachable"])
        self.assertEqual(result["connectionStatus"], "invalid_config")
        self.assertEqual(result["diagnostics"][0]["code"], "source.root_path_required")

    def test_create_source_preserves_unknown_fields_through_config(self):
        store = SourceStore()

        created = store.create_source(
            {
                "name": "Local Samples",
                "sourceType": "local_repo",
                "config": {"rootPath": "/tmp/samples", "futureFlag": True},
            }
        )

        self.assertEqual(created["config"]["futureFlag"], True)
        self.assertEqual(store.get_source(created["sourceId"]).config["futureFlag"], True)

    def test_create_source_rejects_blank_required_fields(self):
        store = SourceStore()

        with self.assertRaises(ConnectionIssue) as raised:
            store.create_source({"name": " ", "sourceType": "local_repo"})

        self.assertEqual(raised.exception.pointer, "#/name")

    def test_source_api_create_invalid_source_returns_problem_response(self):
        response = self.source_api().create_source({"name": " ", "sourceType": "local_repo"}, "trace_create")

        self.assertEqual(response["status"], 422)
        self.assertEqual(response["contentType"], "application/problem+json")
        self.assertEqual(response["body"]["errors"][0]["pointer"], "#/name")

    def test_create_source_rejects_blank_explicit_source_id(self):
        store = SourceStore()

        with self.assertRaises(ConnectionIssue) as raised:
            store.create_source({"sourceId": " ", "name": "Local", "sourceType": "local_repo"})

        self.assertEqual(raised.exception.pointer, "#/sourceId")

    def test_create_source_rejects_duplicate_source_id(self):
        store = SourceStore([{"sourceId": "source_local", "name": "Local", "sourceType": "local_repo"}])

        with self.assertRaises(ConnectionIssue) as raised:
            store.create_source({"sourceId": "source_local", "name": "Other", "sourceType": "local_repo"})

        self.assertEqual(raised.exception.status, 409)


if __name__ == "__main__":
    unittest.main()
