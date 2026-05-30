from __future__ import annotations

import json
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


ROOT = Path(__file__).resolve().parents[1]


def fixed_clock() -> datetime:
    return datetime(2026, 5, 30, 12, 0, tzinfo=UTC)


class SourceConnectionScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "contracts/mocks/sourceConnectionScenarios.json").open(encoding="utf-8") as file:
            cls.fixtures = [json.load(file)]
        with (ROOT / "contracts/mocks/sourceConnectionProbeScenarios.json").open(encoding="utf-8") as file:
            cls.fixtures.append(json.load(file))

    def test_scenario_fixture_uses_contract_envelope(self):
        total = 0
        for fixture in self.fixtures:
            self.assertIn("data", fixture)
            self.assertIn("meta", fixture)
            self.assertEqual(fixture["meta"]["contractVersion"], "0.1.0")
            total += len(fixture["data"])
        self.assertGreaterEqual(total, 16)

    def test_mock_scenarios_match_backend_behavior(self):
        sources = default_sources()
        sources.extend(
            scenario["source"]
            for fixture in self.fixtures
            for scenario in fixture["data"]
            if "source" in scenario
        )
        store = SourceStore(sources)
        service = SourceConnectionService(store, ConnectionPolicy(), fixed_clock)
        app = SourceHttpApp(SourceApi(service, fixed_clock), lambda: "trace_scenario", fixed_clock)

        for fixture in self.fixtures:
            for scenario in fixture["data"]:
                self._assert_scenario(app, scenario)

    def _assert_scenario(self, app: SourceHttpApp, scenario: dict):
        with self.subTest(scenario=scenario["scenarioId"]):
            request = scenario["request"]
            expected = scenario["expected"]
            response = app.handle(request["method"], request["path"])

            self.assertEqual(response["status"], expected["httpStatus"])
            self.assertEqual(response["headers"]["X-Contract-Version"], "0.1.0")
            if expected.get("contentType") == "application/problem+json":
                self.assertEqual(response["contentType"], "application/problem+json")
                self.assertEqual(response["body"]["status"], expected["problemStatus"])
                return

            data = response["body"]["data"]
            diagnostic_codes = [item["code"] for item in data["diagnostics"]]
            self.assertEqual(response["contentType"], "application/json")
            self.assertEqual(data["reachable"], expected["reachable"])
            self.assertEqual(data["connectionStatus"], expected["connectionStatus"])
            self.assertEqual(diagnostic_codes, expected["diagnosticCodes"])
            self.assertEqual(response["body"]["meta"]["partial"], expected["partial"])

    def test_credential_scenario_does_not_echo_secret_like_value(self):
        sources = default_sources()
        sources.extend(
            scenario["source"]
            for fixture in self.fixtures
            for scenario in fixture["data"]
            if scenario["scenarioId"] == "unsafe-reference-credentials"
        )
        store = SourceStore(sources)
        service = SourceConnectionService(store, ConnectionPolicy(), fixed_clock)
        app = SourceHttpApp(SourceApi(service, fixed_clock), lambda: "trace_scenario", fixed_clock)

        response = app.handle("POST", "/api/sources/source_credential_reference/connect-test")

        self.assertEqual(response["body"]["data"]["connectionStatus"], "unsafe_reference")
        self.assertNotIn("token", json.dumps(response["body"]))


if __name__ == "__main__":
    unittest.main()
