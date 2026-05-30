# Technical Requirements Document

## Current Technical Scope

This repository is initialized for documentation, collaboration, and contract-first parallel delivery. The approved technical baseline is the tolerant REST contract in `contracts/openapi.yaml`, its split schemas in `contracts/schemas/`, mock fixtures in `contracts/mocks/`, and a Python backend source connection vertical slice for metadata-only sample source validation.

No frontend runtime, HTTP backend framework, database, queue, external production API integration, authentication, authorization, or deployment path is approved yet.

## Technical Principles

- Keep implementation changes small, testable, and reversible.
- Prefer explicit boundaries between source connectors, classification, review workflow, audit logging, and presentation.
- Inject external collaborators into core logic instead of constructing them inside core modules.
- Keep side effects at boundary layers.
- Use behavior tests for user-observable contracts.
- Keep frontend and backend aligned through `OpenAPI-first + mock-first + vertical-slice-first`.
- Treat unknown fields and enum-like values as forward-compatible.

## Future Boundary Candidates

These are not approved implementation modules yet. They are candidate boundaries to evaluate before coding:

- Source connector boundary.
- Document extraction boundary.
- Finding classification boundary.
- Risk scoring boundary.
- Owner resolution boundary.
- Human review workflow boundary.
- Audit event boundary.
- Delta scan boundary.
- Evaluation harness boundary.
- Admin metrics boundary.
- Governance configuration boundary.
- Permission boundary boundary.
- Review support boundary.

## Contract Baseline

- Base path: `/api`.
- Envelope: `data`, `meta`, and optional `pagination`.
- Error format: `application/problem+json`.
- State machines: scan, finding review, and contract lifecycle are documented in `docs/API_CONTRACT.md` and `docs/design/frontend-backend-delivery-contract.md`.
- Mocks are contract fixtures, not production seed data.
- Governance configuration is documented in `docs/GOVERNANCE_CONFIG.md`.
- Adaptive policy and review state machines are documented in `docs/design/adaptive-governance-review-control.md`.
- Sample source connection validation is documented in `docs/design/sample-source-connection.md`.

## Source Connection Baseline

- The backend source connection core is side-effect-free and uses only the Python standard library.
- A framework-neutral source API adapter returns contract envelopes, response headers, and RFC 9457 problem payloads for source list, create, and connection-test operations.
- A framework-neutral HTTP route boundary handles `GET /api/health`, `GET /api/sources`, `POST /api/sources`, and `POST /api/sources/{sourceId}/connect-test`.
- A standard-library mock HTTP server can expose the source connection routes locally for frontend contract testing.
- The default organizer sample source is metadata-only and references the public repository without vendoring PDFs.
- Local sources are only reachable when their resolved paths stay within explicitly configured allowed roots.
- Mock sources must state that they are mock-only and must not imply production tenant access.
- Connection results return required contract fields plus optional diagnostics, capabilities, source version, and metadata fingerprint.
- Realistic source connection scenario mocks live in `contracts/mocks/sourceConnectionScenarios.json` and `contracts/mocks/sourceConnectionProbeScenarios.json`, and are validated against backend behavior.

Local source connection mock server:

```bash
python3 -m backend.datasentinel.source_server --host 127.0.0.1 --port 8000
```

## External Research Required Before Implementation

Official or authoritative documentation must be reviewed before integrating:

- Microsoft Graph or any file-source API.
- GDPR deletion, retention, or audit-related workflow assumptions.
- The organizer sample repository before downloading or vendoring sample files.
- Any AI, OCR, document parsing, or classification dependency.
- Any storage, authentication, authorization, or deployment platform.

## Technical Done When

The first implementation task has:

- A narrow acceptance criterion.
- A documented impact surface.
- A state machine if it introduces workflow, permissions, asynchronous work, or external protocols.
- Targeted validation commands.
