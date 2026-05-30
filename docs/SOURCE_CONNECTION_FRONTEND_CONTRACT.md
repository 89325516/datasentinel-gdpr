# Source Connection Frontend Contract

## Purpose

This document gives frontend implementers the exact contract for the source connector surface. It is a companion to `docs/API_CONTRACT.md`, `contracts/openapi.yaml`, `contracts/mocks/sourceConnectionScenarios.json`, and `contracts/mocks/sourceConnectionProbeScenarios.json`.

## Supported P0 Routes

| Method | Path | Frontend Use |
| --- | --- | --- |
| `GET` | `/api/health` | Show backend readiness or local mock readiness. |
| `GET` | `/api/sources` | Render available demo sources. |
| `POST` | `/api/sources` | Register a local, organizer sample, or mock source. |
| `POST` | `/api/sources/{sourceId}/connect-test` | Validate source connection before scan start. |

All successful responses are JSON envelopes with `data` and `meta`. Errors use `application/problem+json`.

## Local Mock Server

Backend provides a standard-library mock server for this source connection slice:

```bash
python3 -m backend.datasentinel.source_server --host 127.0.0.1 --port 8000
```

Frontend developers can target `http://127.0.0.1:8000/api` for the routes in this document. The server is for local contract and mock testing only; it is not a production runtime.

## Required UI States

| Status | Meaning | Frontend Behavior |
| --- | --- | --- |
| `connected` | Source is usable for its stated capabilities. | Enable scan start for the allowed scan types. |
| `degraded` | Source is reachable, but metadata or content readiness is incomplete. | Render warning details and require explicit user awareness before scan start. |
| `invalid_config` | Source config is malformed or incomplete. | Keep scan start disabled and show the first diagnostic message. |
| `unsafe_reference` | Source reference violates the approved safety boundary. | Keep scan start disabled and show a security-oriented error state. |
| `policy_denied` | Local path or future permission boundary denies access. | Keep scan start disabled and show the denial reason. |
| `not_found` | Source path or future remote source is missing. | Show retryable or operator-action guidance based on `diagnostics[].retryable`. |
| `permission_denied` | Backend cannot read the local source path. | Show access-denied guidance and leave scan start disabled. |
| `unsupported_type` | Backend does not support the source type in P0. | Render neutral unsupported state, not a crash. |
| `network_error` | Future live probe failed transiently. | Show retry affordance when diagnostics mark the issue retryable. |
| `rate_limited` | Future live probe was throttled by the remote service. | Show retry guidance and leave scan start disabled. |

Unknown status strings must render as a neutral `unknown` state.

## Connection Result Fields

Frontend should rely on:

- `data.sourceId`
- `data.reachable`
- `data.message`
- `data.connectionStatus`
- `data.capabilities.canReadMetadata`
- `data.capabilities.canReadContent`
- `data.capabilities.supportsDeltaScan`
- `data.capabilities.requiresCredentials`
- `data.diagnostics[].code`
- `data.diagnostics[].severity`
- `data.diagnostics[].message`
- `data.diagnostics[].retryable`
- `meta.partial`
- `meta.warnings[]`

Frontend must not assume:

- `connectionStatus` is a closed enum.
- `diagnostics` is non-empty.
- `sourceVersion` always exists.
- `contentFingerprint` is user-displayable text.
- `canReadContent = true` means production tenant access exists.

## Mock Scenario Contract

Use `contracts/mocks/sourceConnectionScenarios.json` and `contracts/mocks/sourceConnectionProbeScenarios.json` for source connector UI state work. The fixtures cover:

- Connected organizer sample source.
- Connected mock SharePoint boundary.
- Connected organizer source using the approved default reference.
- Degraded missing sample family metadata.
- Degraded unknown and duplicate sample family metadata.
- Unsafe non-HTTPS reference.
- Unsafe credential-bearing reference.
- Unsafe wrong host.
- Unsafe wrong repository.
- Unsafe query or fragment selector.
- Simulated network timeout.
- Simulated TLS validation failure.
- Simulated remote rate limit.
- Simulated remote not found.
- Simulated redirect requiring approval.
- Invalid deterministic probe configuration.
- Unsupported future source type.
- Unknown source problem response.

The frontend should render every scenario without throwing, hiding the reason, or displaying raw secrets.

## Scan Start Gate

The source connector surface should only enable scan start when:

- `reachable = true`
- `connectionStatus = connected`, or the user has explicitly acknowledged `degraded`
- `capabilities.canReadMetadata = true`

The frontend must keep scan start disabled for `unsafe_reference`, `policy_denied`, `invalid_config`, `not_found`, `permission_denied`, `unsupported_type`, `network_error`, `rate_limited`, and unknown statuses.

## Security Rules

- Never render credentials or raw source content.
- Prefer diagnostic messages over raw config fields for user-facing copy.
- Show mock-only boundaries clearly.
- Treat `meta.partial = true` as renderable with visible warning state.
