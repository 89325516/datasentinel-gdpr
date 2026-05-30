# API Contract

## Purpose

This contract lets frontend and backend agents work in parallel without blocking each other. It is intentionally broad and tolerant for the hackathon prototype while still giving stable shapes for UI, backend, mocks, and tests.

Source of truth:

- Machine-readable contract: `contracts/openapi.yaml`.
- Mock payloads: `contracts/mocks/`.
- Design rationale: `docs/design/frontend-backend-delivery-contract.md`.
- Adaptive governance rationale: `docs/design/adaptive-governance-review-control.md`.
- Source connector frontend contract: `docs/SOURCE_CONNECTION_FRONTEND_CONTRACT.md`.

## Standard Basis

- OpenAPI 3.1 describes HTTP APIs and aligns schema objects with JSON Schema 2020-12: https://spec.openapis.org/oas/v3.1.0.html
- JSON Schema allows additional object properties by default and can model extension-friendly objects: https://json-schema.org/understanding-json-schema/reference/object
- RFC 9457 defines `application/problem+json` for HTTP API error details: https://www.rfc-editor.org/rfc/rfc9457.html

## Contract Strategy

Use `OpenAPI-first + mock-first + vertical-slice-first`.

- OpenAPI-first: all endpoint shapes are documented before implementation.
- Mock-first: frontend can render the full P0 flow from static payloads.
- Vertical-slice-first: backend should implement one complete source -> scan -> finding -> review -> audit path before broad feature work.

## Wire Format

- Base path: `/api`.
- JSON field names: lower camel case.
- IDs are opaque strings, such as `scan_001`.
- Dates use ISO 8601 UTC strings.
- Money, legal conclusions, and raw sensitive values are not part of P0 payloads.
- Sensitive snippets must be redacted.

## Response Envelope

Every successful response returns:

```json
{
  "data": {},
  "meta": {
    "contractVersion": "0.1.0",
    "generatedAt": "2026-05-30T12:00:00Z",
    "traceId": "trace_demo_001",
    "partial": false,
    "warnings": []
  }
}
```

List responses may also include:

```json
{
  "pagination": {
    "limit": 25,
    "offset": 0,
    "total": 42,
    "nextCursor": null
  }
}
```

## Tolerance Rules

- Clients must ignore unknown fields.
- Servers may add optional fields without changing the contract version.
- Clients must handle missing optional fields, `null` optional objects, and empty arrays.
- Enum-like values are open strings. Unknown values must render as `unknown` or a neutral fallback.
- Numeric metrics may be `null` while a scan is running.
- `meta.partial = true` means the UI may render available data with a warning.
- Backend should preserve stable IDs within a demo seed.
- Permission-aware endpoints should return both allowed and denied actions when available.
- Policy guidance should include policy-pack version, not hard-coded legal conclusions.

## Required Headers

Requests should send:

- `Accept: application/json, application/problem+json`
- `X-Contract-Version: 0.1.0`
- `X-Actor-Id: user_demo_admin` or a seeded demo user.
- `Idempotency-Key` for review actions and scan start requests when available.

Responses should include:

- `X-Trace-Id`
- `X-Contract-Version`

## Error Format

Errors use `application/problem+json`.

```json
{
  "type": "https://datasentinel.local/problems/validation-error",
  "title": "Request validation failed",
  "status": 422,
  "detail": "The request body is invalid.",
  "instance": "/api/scans/full",
  "traceId": "trace_demo_001",
  "errors": [
    {
      "pointer": "#/sourceId",
      "detail": "sourceId is required"
    }
  ]
}
```

## P0 Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Check backend readiness. |
| `GET` | `/api/sources` | List configured sources. |
| `POST` | `/api/sources` | Create a local or mock source. |
| `POST` | `/api/sources/{sourceId}/connect-test` | Validate source reachability. |
| `POST` | `/api/scans/full` | Start a full scan. |
| `POST` | `/api/scans/delta` | Start a delta scan. |
| `GET` | `/api/scans/{scanId}` | Read scan status and progress. |
| `GET` | `/api/scans/{scanId}/summary` | Read KPI summary for one scan. |
| `GET` | `/api/findings` | List findings for admin or owner views. |
| `GET` | `/api/findings/{findingId}` | Read an evidence card. |
| `POST` | `/api/findings/{findingId}/review` | Record a human review decision. |
| `GET` | `/api/audit/events` | List audit events. |
| `GET` | `/api/admin/metrics` | Read admin dashboard metrics. |
| `GET` | `/api/evaluation/runs/latest` | Read latest evaluation summary. |
| `GET` | `/api/governance/config` | Read active governance configuration. |
| `GET` | `/api/governance/policy-packs/active` | Read active policy pack. |
| `POST` | `/api/governance/changes/preview` | Preview policy or organization change impact. |
| `GET` | `/api/users/me/permissions` | Read current actor permission boundary. |
| `GET` | `/api/findings/{findingId}/review-support` | Read reviewer guidance and allowed actions. |

## State Machines

### Scan Status

`queued -> running -> completed`

Failure paths:

- `queued -> failed`
- `running -> failed`
- `running -> cancelled`

Retry path:

- `failed -> queued`

### Source Connection Status

Connection testing is side-effect-free. It validates metadata and boundaries before scans start.

Primary paths:

- `registered -> validating -> connected`
- `registered -> validating -> degraded`

Failure paths:

- `registered -> validating -> invalid_config`
- `registered -> validating -> unsafe_reference`
- `registered -> validating -> policy_denied`
- `registered -> validating -> not_found`
- `registered -> validating -> unsupported_type`
- `registered -> validating -> network_error`
- `registered -> validating -> rate_limited`

Unknown source IDs use `application/problem+json` with 404 semantics.

### Finding Status

`open -> assigned -> under_review -> reviewed -> closed`

Alternative terminal statuses:

- `false_positive`
- `escalated`
- `delete_candidate`
- `retained`

### Review Decisions

Allowed P0 decisions:

- `delete_candidate`
- `keep_with_reason`
- `correct_false_positive`
- `reassign_owner`
- `escalate`

Every review decision requires `reason`.

### Governance Policy Status

`draft -> validating -> pending_activation -> active -> superseded`

Rollback path:

- `active -> rolled_back`

### Task Transfer

`assigned -> transfer_pending -> assigned`

Failure path:

- `transfer_pending -> assigned` when the target rejects the task.

## Organizer Sample Source

Default demo source:

```text
https://github.com/a-klumpp/GDPR-data-samples
```

The contract represents the source as `sourceType = organizer_sample_repo` and exposes sample families as metadata. The repository content is referenced, not vendored.

`POST /api/sources/{sourceId}/connect-test` keeps `sourceId`, `reachable`, and `message` as the required result shape. It may also return optional diagnostics:

- `connectionStatus`: open string such as `connected`, `degraded`, `invalid_config`, `unsafe_reference`, `policy_denied`, `not_found`, `unsupported_type`, `network_error`, or `rate_limited`.
- `checkedAt`: ISO 8601 UTC timestamp for this connection test.
- `capabilities`: `canReadMetadata`, `canReadContent`, `supportsDeltaScan`, and `requiresCredentials`.
- `diagnostics`: ordered objects with `code`, `severity`, `message`, and `retryable`.
- `sourceVersion`: source metadata version such as a commit SHA when known.
- `contentFingerprint`: metadata-only fingerprint. It must not expose raw sample file content.

Backend-owned source connection routes currently implemented for this vertical slice:

- `GET /api/health`
- `GET /api/sources`
- `POST /api/sources`
- `POST /api/sources/{sourceId}/connect-test`

The backend route boundary is framework-neutral and returns the same envelope, headers, and problem content types that a future HTTP framework adapter must preserve.

## Mock Payloads

Frontend agents should begin with:

- `contracts/mocks/adminMetrics.json`
- `contracts/mocks/auditEvents.json`
- `contracts/mocks/connectionTest.json`
- `contracts/mocks/evaluationLatest.json`
- `contracts/mocks/findingDetail.json`
- `contracts/mocks/governanceConfig.json`
- `contracts/mocks/myFindings.json`
- `contracts/mocks/permissionBoundary.json`
- `contracts/mocks/reviewSupport.json`
- `contracts/mocks/scanStatus.json`
- `contracts/mocks/sources.json`
- `contracts/mocks/sourceConnectionScenarios.json`
- `contracts/mocks/sourceConnectionProbeScenarios.json`

Mocks are contract fixtures. They are not production seed data.

## Breaking Changes

Breaking changes require a documented contract version bump:

- Removing a field currently marked required.
- Renaming a field.
- Changing an ID, date, boolean, object, array, or number into another type.
- Closing an enum-like string so unknown values fail.
- Changing endpoint semantics.
- Changing review or scan state transitions.
