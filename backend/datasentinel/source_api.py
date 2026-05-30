from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Mapping

from .source_constants import CONTRACT_VERSION
from .source_connection import SourceConnectionService
from .source_result import ConnectionIssue, isoformat, problem_from_issue, utc_now


class SourceApi:
    def __init__(
        self,
        service: SourceConnectionService,
        clock: Callable[[], datetime] = utc_now,
    ):
        self._service = service
        self._clock = clock

    def list_sources(self, trace_id: str) -> dict[str, Any]:
        return self._success(
            200,
            {
                "data": self._service.list_sources(),
                "meta": self._meta(trace_id),
            },
            trace_id,
        )

    def create_source(self, payload: Mapping[str, Any], trace_id: str) -> dict[str, Any]:
        try:
            source = self._service.create_source(payload)
        except ConnectionIssue as issue:
            return self._problem(issue, "/api/sources", trace_id)

        return self._success(
            201,
            {
                "data": source,
                "meta": self._meta(trace_id),
            },
            trace_id,
        )

    def test_connection(self, source_id: str, trace_id: str) -> dict[str, Any]:
        instance = f"/api/sources/{source_id}/connect-test"
        try:
            body = self._service.connection_envelope(source_id, trace_id)
        except ConnectionIssue as issue:
            return self._problem(issue, instance, trace_id)

        return self._success(200, body, trace_id)

    def _success(self, status: int, body: Mapping[str, Any], trace_id: str) -> dict[str, Any]:
        return {
            "status": status,
            "contentType": "application/json",
            "headers": {
                "X-Trace-Id": trace_id,
                "X-Contract-Version": CONTRACT_VERSION,
            },
            "body": dict(body),
        }

    def _problem(self, issue: ConnectionIssue, instance: str, trace_id: str) -> dict[str, Any]:
        return {
            "status": issue.status,
            "contentType": "application/problem+json",
            "headers": {
                "X-Trace-Id": trace_id,
                "X-Contract-Version": CONTRACT_VERSION,
            },
            "body": problem_from_issue(issue, instance, trace_id),
        }

    def _meta(self, trace_id: str) -> dict[str, Any]:
        return {
            "contractVersion": CONTRACT_VERSION,
            "generatedAt": isoformat(self._clock()),
            "traceId": trace_id,
            "partial": False,
            "warnings": [],
        }
