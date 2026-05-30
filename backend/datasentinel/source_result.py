from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping

from .source_constants import CONTRACT_VERSION


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    message: str
    retryable: bool

    def to_contract(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "retryable": self.retryable,
        }


class ConnectionIssue(ValueError):
    def __init__(self, code: str, detail: str, pointer: str = "#", status: int = 422):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.pointer = pointer
        self.status = status


def connection_result(
    source_id: str,
    reachable: bool,
    status: str,
    message: str,
    diagnostics: list[Diagnostic],
    capabilities: Mapping[str, bool],
    source_version: str | None = None,
    content_fingerprint: str | None = None,
    checked_at: datetime | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "sourceId": source_id,
        "reachable": reachable,
        "message": message,
        "connectionStatus": status,
        "checkedAt": isoformat(checked_at or utc_now()),
        "capabilities": dict(capabilities),
        "diagnostics": [item.to_contract() for item in diagnostics],
    }
    if source_version:
        data["sourceVersion"] = source_version
    if content_fingerprint:
        data["contentFingerprint"] = content_fingerprint
    return data


def capabilities(
    metadata: bool = False,
    content: bool = False,
    delta: bool = False,
) -> dict[str, bool]:
    return {
        "canReadMetadata": metadata,
        "canReadContent": content,
        "supportsDeltaScan": delta,
        "requiresCredentials": False,
    }


def diagnostic(code: str, severity: str, message: str, retryable: bool) -> Diagnostic:
    return Diagnostic(code=code, severity=severity, message=message, retryable=retryable)


def problem_from_issue(issue: ConnectionIssue, instance: str, trace_id: str) -> dict[str, Any]:
    return {
        "type": f"https://datasentinel.local/problems/{issue.code.replace('.', '-')}",
        "title": problem_title(issue.status),
        "status": issue.status,
        "detail": issue.detail,
        "instance": instance,
        "traceId": trace_id,
        "errors": [
            {
                "pointer": issue.pointer,
                "detail": issue.detail,
            }
        ],
    }


def problem_title(status: int) -> str:
    if status == 404:
        return "Source not found"
    if status == 409:
        return "Source conflict"
    return "Request validation failed"


def envelope_meta(data: Mapping[str, Any], generated_at: datetime, trace_id: str) -> dict[str, Any]:
    return {
        "contractVersion": CONTRACT_VERSION,
        "generatedAt": isoformat(generated_at),
        "traceId": trace_id,
        "partial": data["connectionStatus"] == "degraded",
        "warnings": [
            item["message"]
            for item in data["diagnostics"]
            if item["severity"] == "warning"
        ],
    }


def utc_now() -> datetime:
    return datetime.now(UTC)


def isoformat(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")

