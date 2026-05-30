# Parallel Delivery Workflow

## Goal

Allow frontend, backend, product, and QA workstreams to move in parallel while sharing one tolerant API contract.

## Workstreams

| Workstream | Owns | Must Not Own |
| --- | --- | --- |
| Contract | OpenAPI, mocks, shared state machines, compatibility rules | UI layout or scanner internals |
| Frontend | Screens, components, route behavior, loading and error states | Backend persistence or scanner decisions |
| Backend | API endpoints, scanner pipeline, evaluation, audit persistence | UI styling or frontend routing |
| Product and QA | Acceptance criteria, demo script, test cases, risk review | Hidden implementation details |

## Branch Pattern

- `contract/*` for OpenAPI, mocks, and contract docs.
- `fe/*` for frontend work.
- `be/*` for backend work.
- `docs/*` for non-contract docs.

## First Two Hours

1. Freeze `contracts/openapi.yaml` at version `0.1.0`.
2. Freeze P0 mock payloads in `contracts/mocks/`.
3. Frontend renders admin metrics, findings list, evidence card, review action, audit timeline, evaluation, permissions, and governance settings from mocks.
4. Backend implements `/api/health` and returns mock-compatible scan, findings, governance, and permissions payloads.
5. QA verifies docs, mocks, and OpenAPI use the same field names.

## Integration Gates

### Gate 1: Mock UI Ready

- Frontend can render the P0 demo flow using only mocks.
- Empty, loading, error, and partial data states are visible.
- Unknown enum-like values do not crash rendering.

### Gate 2: Backend Contract Ready

- Backend exposes every P0 endpoint in the OpenAPI contract.
- Backend returns the response envelope and problem details format.
- Backend accepts `X-Actor-Id` for demo role simulation.

### Gate 3: First Vertical Slice

- `POST /api/scans/full` creates a scan.
- `GET /api/scans/{scanId}` reports status.
- `GET /api/findings` returns at least one finding.
- `GET /api/findings/{findingId}` returns evidence.
- `POST /api/findings/{findingId}/review` records a decision.
- `GET /api/audit/events` includes the review event.
- `GET /api/users/me/permissions` returns allowed and denied actions.
- `GET /api/findings/{findingId}/review-support` returns checklist, transfer, and escalation support.

### Gate 4: Evaluation and Demo Confidence

- Admin metrics show scanned files, flagged files, volume, progress, time, review backlog, and high-risk count.
- Evaluation shows precision, recall, F1, reproducibility, throughput, and resource intensity.
- Deletion remains simulated.
- Governance settings show active policy-pack version and source adapter readiness.
- The organizer sample source appears as the default demo source.

## AI Task Brief Template

```markdown
Goal:
Context:
Constraints:
Contract Impact:
Done when:
Validation:
```

## Frontend Agent Rules

- Start from `contracts/mocks/`.
- For source connector UI states, start from `contracts/mocks/sourceConnectionScenarios.json`, `contracts/mocks/sourceConnectionProbeScenarios.json`, and `docs/SOURCE_CONNECTION_FRONTEND_CONTRACT.md`.
- When a live local mock is useful, point the frontend at the standard-library source mock server from `backend.datasentinel.source_server`.
- Keep UI resilient to missing optional fields.
- Treat `meta.partial = true` as renderable with a warning.
- Never display raw sensitive values.
- Do not add endpoint assumptions outside `docs/API_CONTRACT.md`.
- Show denied actions with reasons instead of silently hiding all unavailable controls.

## Backend Agent Rules

- Match `contracts/openapi.yaml` first.
- Keep endpoint responses envelope-wrapped.
- Use `application/problem+json` for errors.
- Preserve source connection route behavior from `backend/datasentinel/source_http.py` when replacing the framework-neutral adapter with a real HTTP framework.
- Preserve real HTTP behavior covered by `tests/test_source_server.py` when replacing the local mock server.
- Make scan and review actions idempotent when `Idempotency-Key` is present.
- Keep real deletion out of P0.
- Return policy-pack version and permission-boundary data when the contract includes it.

## QA Agent Rules

- Validate English-only tracked docs and fixtures.
- Compare OpenAPI fields, docs, and mocks.
- Run source connector scenario coverage against `contracts/mocks/sourceConnectionScenarios.json` and `contracts/mocks/sourceConnectionProbeScenarios.json`.
- Check that state transitions match `docs/API_CONTRACT.md`.
- Confirm that every acceptance change is reflected in `ACCEPTANCE.md`.
