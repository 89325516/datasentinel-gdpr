from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import urlparse

from .source_constants import (
    EXPECTED_SAMPLE_FAMILIES,
    ORGANIZER_REFERENCE_URL,
    ORGANIZER_REPO_VERSION,
)
from .source_result import (
    Diagnostic,
    capabilities,
    connection_result,
    diagnostic,
    envelope_meta,
    utc_now,
)
from .source_store import SourceRecord, SourceStore


@dataclass(frozen=True)
class ConnectionPolicy:
    allowed_local_roots: tuple[Path, ...] = ()
    default_reference_url: str = ORGANIZER_REFERENCE_URL
    expected_families: tuple[str, ...] = EXPECTED_SAMPLE_FAMILIES

    @classmethod
    def with_roots(cls, roots: Iterable[Path]) -> "ConnectionPolicy":
        return cls(allowed_local_roots=tuple(root.resolve() for root in roots))


class SourceConnectionService:
    def __init__(
        self,
        store: SourceStore,
        policy: ConnectionPolicy = ConnectionPolicy(),
        clock: Callable[[], datetime] = utc_now,
    ):
        self._store = store
        self._policy = policy
        self._clock = clock

    def connection_envelope(self, source_id: str, trace_id: str) -> dict:
        data = self.test_connection(source_id)
        return {
            "data": data,
            "meta": envelope_meta(data, self._clock(), trace_id),
        }

    def list_sources(self) -> list[dict[str, Any]]:
        return self._store.list_sources()

    def create_source(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self._store.create_source(payload)

    def test_connection(self, source_id: str) -> dict:
        source = self._store.get_source(source_id)
        if source.source_type == "organizer_sample_repo":
            return self._test_organizer_source(source)
        if source.source_type == "sharepoint_mock":
            return self._mock_connection(source)
        if source.source_type in {"local_repo", "local_directory"}:
            return self._test_local_source(source)
        return self._result(
            source.source_id,
            False,
            "unsupported_type",
            "Source type is not supported in P0.",
            [diagnostic("source.unsupported_type", "warning", "The source type is not supported in P0.", False)],
            capabilities(),
        )

    def _test_organizer_source(self, source: SourceRecord) -> dict:
        diagnostics: list[Diagnostic] = []
        reference_url = source.reference_url
        if not reference_url:
            reference_url = self._policy.default_reference_url
            diagnostics.append(
                diagnostic(
                    "source.default_reference_used",
                    "info",
                    "Default organizer sample reference was used.",
                    False,
                )
            )

        unsafe = _organizer_reference_issue(reference_url)
        if unsafe:
            return self._result(
                source.source_id,
                False,
                "unsafe_reference",
                unsafe.message,
                [unsafe],
                capabilities(),
            )

        family_diagnostics = _sample_family_diagnostics(
            source.sample_families,
            self._policy.expected_families,
        )
        diagnostics.extend(family_diagnostics)
        status = "degraded" if any(item.severity == "warning" for item in diagnostics) else "connected"
        return self._result(
            source.source_id,
            True,
            status,
            "Organizer sample source metadata is reachable.",
            diagnostics,
            capabilities(metadata=True, delta=True),
            source_version=source.to_contract().get("sourceVersion", ORGANIZER_REPO_VERSION),
            content_fingerprint=_metadata_fingerprint(reference_url, source.sample_families),
        )

    def _mock_connection(self, source: SourceRecord) -> dict:
        return self._result(
            source.source_id,
            True,
            "connected",
            "Mock source is available for metadata-only P0 workflows.",
            [
                diagnostic(
                    "source.mock_only",
                    "info",
                    "This source is a mock and does not represent a production tenant.",
                    False,
                )
            ],
            capabilities(metadata=True),
        )

    def _test_local_source(self, source: SourceRecord) -> dict:
        root_path = source.config.get("rootPath")
        if not isinstance(root_path, str) or not root_path.strip():
            return self._result(
                source.source_id,
                False,
                "invalid_config",
                "Local source requires config.rootPath.",
                [diagnostic("source.root_path_required", "error", "config.rootPath is required.", False)],
                capabilities(),
            )

        path = Path(root_path).expanduser()
        if not path.is_absolute():
            return self._result(
                source.source_id,
                False,
                "invalid_config",
                "Local source rootPath must be absolute.",
                [diagnostic("source.root_path_relative", "error", "rootPath must be absolute.", False)],
                capabilities(),
            )

        resolved = path.resolve(strict=False)
        if not _is_allowed_path(resolved, self._policy.allowed_local_roots):
            return self._result(
                source.source_id,
                False,
                "policy_denied",
                "Local source is outside allowed roots.",
                [diagnostic("source.root_path_denied", "error", "rootPath is outside allowed roots.", False)],
                capabilities(),
            )

        if not resolved.exists():
            return self._result(
                source.source_id,
                False,
                "not_found",
                "Local source path does not exist.",
                [diagnostic("source.root_path_missing", "error", "rootPath does not exist.", True)],
                capabilities(),
            )
        if not resolved.is_dir():
            return self._result(
                source.source_id,
                False,
                "invalid_config",
                "Local source path is not a directory.",
                [diagnostic("source.root_path_not_directory", "error", "rootPath is not a directory.", False)],
                capabilities(),
            )

        try:
            has_entries = any(resolved.iterdir())
        except (PermissionError, OSError):
            return self._permission_denied(source.source_id)

        if not has_entries:
            return self._result(
                source.source_id,
                True,
                "degraded",
                "Local source is reachable but empty.",
                [diagnostic("source.local_empty", "warning", "Local source contains no visible entries.", False)],
                capabilities(metadata=True, content=True, delta=True),
            )

        return self._result(
            source.source_id,
            True,
            "connected",
            "Local source directory is reachable.",
            [],
            capabilities(metadata=True, content=True, delta=True),
        )

    def _permission_denied(self, source_id: str) -> dict:
        return self._result(
            source_id,
            False,
            "permission_denied",
            "Local source directory cannot be read.",
            [diagnostic("source.root_path_unreadable", "error", "rootPath cannot be read.", True)],
            capabilities(),
        )

    def _result(
        self,
        source_id: str,
        reachable: bool,
        status: str,
        message: str,
        diagnostics: list[Diagnostic],
        source_capabilities: dict[str, bool],
        source_version: str | None = None,
        content_fingerprint: str | None = None,
    ) -> dict:
        return connection_result(
            source_id,
            reachable,
            status,
            message,
            diagnostics,
            source_capabilities,
            source_version,
            content_fingerprint,
            self._clock(),
        )


def _organizer_reference_issue(reference_url: str) -> Diagnostic | None:
    parsed = urlparse(reference_url)
    path = parsed.path.rstrip("/")
    if parsed.scheme != "https":
        return diagnostic("source.reference_scheme", "error", "Organizer sample reference must use HTTPS.", False)
    if parsed.username or parsed.password:
        return diagnostic("source.reference_credentials", "error", "Organizer sample reference must not contain credentials.", False)
    if parsed.netloc.lower() != "github.com":
        return diagnostic("source.reference_host", "error", "Organizer sample reference must use github.com.", False)
    if parsed.query or parsed.fragment:
        return diagnostic("source.reference_selector", "error", "Organizer sample reference must not contain query or fragment.", False)
    if path.endswith(".git"):
        path = path[:-4]
    if path != "/a-klumpp/GDPR-data-samples":
        return diagnostic("source.reference_repo", "error", "Organizer sample reference must target the approved repository.", False)
    return None


def _sample_family_diagnostics(families: list[str], expected: tuple[str, ...]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    family_set = set(families)
    missing = [family for family in expected if family not in family_set]
    extras = [family for family in families if family not in expected]
    duplicates = sorted({family for family in families if families.count(family) > 1})
    if missing:
        diagnostics.append(
            diagnostic(
                "source.sample_family_missing",
                "warning",
                f"Missing expected sample families: {', '.join(missing)}.",
                False,
            )
        )
    if extras:
        diagnostics.append(
            diagnostic(
                "source.sample_family_unknown",
                "warning",
                f"Unknown sample families were provided: {', '.join(extras)}.",
                False,
            )
        )
    if duplicates:
        diagnostics.append(
            diagnostic(
                "source.sample_family_duplicate",
                "warning",
                f"Duplicate sample families were provided: {', '.join(duplicates)}.",
                False,
            )
        )
    return diagnostics


def _is_allowed_path(path: Path, allowed_roots: tuple[Path, ...]) -> bool:
    if not allowed_roots:
        return False
    for root in allowed_roots:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def _metadata_fingerprint(reference_url: str, families: list[str]) -> str:
    family_part = ",".join(sorted(families))
    digest = hashlib.sha256(f"{reference_url}\n{family_part}".encode("utf-8")).hexdigest()
    return f"metadata:sha256:{digest}"
