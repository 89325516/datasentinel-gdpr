from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Callable, Mapping
from urllib.parse import unquote, urlparse

from .source_api import SourceApi
from .source_constants import CONTRACT_VERSION
from .source_result import isoformat, utc_now


class SourceHttpApp:
    def __init__(
        self,
        api: SourceApi,
        trace_factory: Callable[[], str] | None = None,
        clock: Callable[[], datetime] = utc_now,
    ):
        self._api = api
        self._trace_factory = trace_factory or _default_trace
        self._clock = clock

    def handle(
        self,
        method: str,
        target: str,
        headers: Mapping[str, str] | None = None,
        body: bytes | str | None = None,
    ) -> dict[str, Any]:
        normalized_headers = _normalize_headers(headers or {})
        trace_id = normalized_headers.get("x-trace-id") or self._trace_factory()
        path = urlparse(target).path

        if method == "GET" and path == "/api/health":
            return self._success(200, {"status": "ok", "serviceVersion": CONTRACT_VERSION}, trace_id)
        if method == "GET" and path == "/api/sources":
            return self._api.list_sources(trace_id)
        if method == "POST" and path == "/api/sources":
            parsed = self._json_body(body, normalized_headers, trace_id, "/api/sources")
            if parsed.get("contentTypeError"):
                return parsed["response"]
            return self._api.create_source(parsed["payload"], trace_id)
        is_connect_path = _is_connect_path(path)
        if method == "POST" and is_connect_path:
            source_id = _source_id_from_path(path)
            if not source_id:
                return _problem(404, "Route not found", "No source ID was provided.", path, trace_id)
            return self._api.test_connection(source_id, trace_id)
        if path == "/api/sources" or is_connect_path:
            return _problem(405, "Method not allowed", "The method is not allowed for this route.", path, trace_id)
        return _problem(404, "Route not found", "The requested route does not exist.", path, trace_id)

    def _json_body(
        self,
        body: bytes | str | None,
        headers: Mapping[str, str],
        trace_id: str,
        instance: str,
    ) -> dict[str, Any]:
        content_type = headers.get("content-type", "")
        if content_type and "application/json" not in content_type:
            return {
                "contentTypeError": True,
                "response": _problem(
                    415,
                    "Unsupported media type",
                    "POST requests must use application/json.",
                    instance,
                    trace_id,
                ),
            }
        if body is None or body == b"" or body == "":
            return {"payload": {}}
        try:
            text = body.decode("utf-8") if isinstance(body, bytes) else body
            payload = json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {
                "contentTypeError": True,
                "response": _problem(
                    400,
                    "Malformed JSON",
                    "Request body must be valid JSON.",
                    instance,
                    trace_id,
                ),
            }
        if not isinstance(payload, dict):
            return {
                "contentTypeError": True,
                "response": _problem(
                    422,
                    "Request validation failed",
                    "Request body must be a JSON object.",
                    instance,
                    trace_id,
                    "#",
                ),
            }
        return {"payload": payload}

    def _success(self, status: int, data: Mapping[str, Any], trace_id: str) -> dict[str, Any]:
        return {
            "status": status,
            "contentType": "application/json",
            "headers": _headers(trace_id),
            "body": {
                "data": dict(data),
                "meta": {
                    "contractVersion": CONTRACT_VERSION,
                    "generatedAt": isoformat(self._clock()),
                    "traceId": trace_id,
                    "partial": False,
                    "warnings": [],
                },
            },
        }


def _source_id_from_path(path: str) -> str:
    prefix = "/api/sources/"
    suffix = "/connect-test"
    segment = path[len(prefix) : -len(suffix)]
    if "/" in segment:
        return ""
    return unquote(segment)


def _is_connect_path(path: str) -> bool:
    return path.startswith("/api/sources/") and path.endswith("/connect-test")


def _problem(
    status: int,
    title: str,
    detail: str,
    instance: str,
    trace_id: str,
    pointer: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": f"https://datasentinel.local/problems/http-{status}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": instance,
        "traceId": trace_id,
    }
    if pointer:
        body["errors"] = [{"pointer": pointer, "detail": detail}]
    return {
        "status": status,
        "contentType": "application/problem+json",
        "headers": _headers(trace_id),
        "body": body,
    }


def _headers(trace_id: str) -> dict[str, str]:
    return {
        "X-Trace-Id": trace_id,
        "X-Contract-Version": CONTRACT_VERSION,
    }


def _normalize_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {str(key).lower(): str(value) for key, value in headers.items()}


def _default_trace() -> str:
    return f"trace_{uuid.uuid4().hex}"
