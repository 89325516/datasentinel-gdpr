from __future__ import annotations

from typing import Any, Iterable, Mapping

from .source_result import ConnectionIssue


class SourceRecord:
    def __init__(self, fields: Mapping[str, Any]):
        self._fields = dict(fields)

    @property
    def source_id(self) -> str:
        return str(self._fields.get("sourceId", ""))

    @property
    def source_type(self) -> str:
        return str(self._fields.get("sourceType", ""))

    @property
    def config(self) -> Mapping[str, Any]:
        value = self._fields.get("config", {})
        return value if isinstance(value, Mapping) else {}

    @property
    def reference_url(self) -> str | None:
        value = self._fields.get("referenceUrl") or self.config.get("referenceUrl")
        return str(value) if value else None

    @property
    def sample_families(self) -> list[str]:
        value = self._fields.get("sampleFamilies")
        if isinstance(value, list):
            return [str(item) for item in value]
        return []

    def to_contract(self) -> dict[str, Any]:
        return dict(self._fields)


class SourceStore:
    def __init__(self, initial_sources: Iterable[Mapping[str, Any]] = ()):
        self._sources: dict[str, SourceRecord] = {}
        for source in initial_sources:
            record = SourceRecord(source)
            self._sources[record.source_id] = record

    def list_sources(self) -> list[dict[str, Any]]:
        return [record.to_contract() for record in self._sources.values()]

    def get_source(self, source_id: str) -> SourceRecord:
        normalized = required_text(source_id, "#/sourceId", "sourceId is required")
        try:
            return self._sources[normalized]
        except KeyError as error:
            raise ConnectionIssue(
                "source.not_found",
                "The requested source does not exist.",
                "#/sourceId",
                404,
            ) from error

    def create_source(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        name = required_text(payload.get("name"), "#/name", "name is required")
        source_type = required_text(
            payload.get("sourceType"),
            "#/sourceType",
            "sourceType is required",
        )
        config = payload.get("config", {})
        if config is not None and not isinstance(config, Mapping):
            raise ConnectionIssue("source.config_invalid", "config must be an object.", "#/config")

        if "sourceId" in payload:
            source_id = required_text(payload.get("sourceId"), "#/sourceId", "sourceId is required")
        else:
            source_id = source_id_from(name, source_type)
        if source_id in self._sources:
            raise ConnectionIssue(
                "source.duplicate",
                "sourceId already exists.",
                "#/sourceId",
                409,
            )

        record = {
            "sourceId": source_id,
            "name": name,
            "sourceType": source_type,
            "status": "registered",
            "masterOfDataUserId": payload.get("masterOfDataUserId"),
            "config": dict(config or {}),
        }
        if "referenceUrl" in payload:
            record["referenceUrl"] = payload["referenceUrl"]
        if "sampleFamilies" in payload:
            families = payload["sampleFamilies"]
            record["sampleFamilies"] = families if isinstance(families, list) else []

        self._sources[source_id] = SourceRecord(record)
        return dict(record)


def required_text(value: Any, pointer: str, detail: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConnectionIssue("source.validation_error", detail, pointer)
    return value.strip()


def source_id_from(name: str, source_type: str) -> str:
    normalized = "".join(ch if ch.isalnum() else "_" for ch in f"{source_type}_{name}".lower())
    return f"source_{normalized.strip('_')}"
