# Sample Source Connection Design

## Problem Definition

The P0 backend needs a reliable way to validate a controlled sample data source before a scan is started. The current contract has `POST /api/sources/{sourceId}/connect-test`, but the response only states whether the source is reachable. That is not enough for strict business conditions where teams need to know why a source is usable, degraded, denied, unsafe, or unsupported.

This design covers metadata-only connection validation for P0 sample sources. It does not download sample PDFs, scan file contents, connect to production Microsoft Graph, perform OAuth, create tenants, or delete data.

## Research Basis

- OpenAPI 3.1 is the source contract format for the API and supports extension-friendly schemas through JSON Schema semantics: https://spec.openapis.org/oas/v3.1.0.html
- RFC 9457 defines the `application/problem+json` error format used for invalid requests and missing sources: https://www.rfc-editor.org/rfc/rfc9457
- GitHub's repository contents API states that public contents can be read without authentication, directory responses have a 1,000-file limit, and download URLs expire and should be refreshed before use: https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28
- The organizer sample repository is referenced as `https://github.com/a-klumpp/GDPR-data-samples`; repository content is referenced, not vendored.

## Scope

In scope:

- Seed the default organizer sample source as a metadata-only backend source.
- Validate source identity, source type, reference URL, sample-family metadata, local path boundaries, and mock-source boundaries.
- Return contract-compatible connection results with explicit diagnostics, capabilities, and warnings.
- Preserve forward compatibility by adding only optional response fields.
- Keep connection tests side-effect-free.

Out of scope:

- Production Microsoft 365, Graph, OAuth, tenant, or permission integration.
- Remote file download, PDF parsing, classification, or scan execution.
- Automatic deletion or legal compliance conclusions.
- Persistent database selection.
- Live external API dependency in behavior tests.

## Options Considered

| Option | Description | Decision |
| --- | --- | --- |
| Metadata-only connector core | Validate configured sample references and local boundaries without downloading files. | Chosen for P0 because it is deterministic, reversible, and matches the demo constraint that live external APIs are not required. |
| Live GitHub contents probe | Call GitHub during every connection test. | Deferred because network, rate limit, TLS, and repository changes would make the demo nondeterministic. The design records these edge cases and keeps a future probe boundary possible. |
| Full HTTP backend framework now | Add a web framework and implement all source endpoints. | Deferred because no runtime dependency has been approved and the current task only needs the backend connection core. |

## State Machine

| State | Event | Guard | Next State | Side Effect |
| --- | --- | --- | --- | --- |
| `unregistered` | Source is created | Required fields are valid | `registered` | Store metadata only |
| `registered` | Connection test requested | Source ID exists | `validating` | Create traceable connection result |
| `registered` | Connection test requested | Source ID is unknown | `failed` | Return `application/problem+json` with 404 semantics |
| `validating` | Reference is safe and metadata is complete | Source type is supported | `connected` | Return reachable result and capabilities |
| `validating` | Reference is safe but metadata is incomplete | Missing optional or expected sample metadata | `degraded` | Return reachable result with warning diagnostics |
| `validating` | Configuration is malformed | Required config is absent or invalid | `invalid_config` | Return unreachable result with validation diagnostics |
| `validating` | Reference is unsafe | URL contains credentials, unsupported host, query, fragment, or path mismatch | `unsafe_reference` | Return unreachable result without touching remote content |
| `validating` | Local boundary is denied | Path escapes allowed roots or symlink resolves outside them | `policy_denied` | Return unreachable result |
| `validating` | Local source is missing | Path does not exist | `not_found` | Return retryable unreachable result |
| `validating` | Permission check fails | Path cannot be read | `permission_denied` | Return retryable or operator-action diagnostic |
| `validating` | External probe reports transient failure | Timeout, DNS, TLS, rate limit, or service error | `degraded` or `network_error` | Return explicit retryability |
| `connected` | Source metadata changes | New source version or family list is observed | `registered` | Require a fresh connection test before scanning |

Rollback path:

- The backend can remove the new optional diagnostic fields while preserving required `sourceId`, `reachable`, and `message` fields.
- The connection core is isolated from scan execution, so disabling it does not require changes to scanner, review, audit, or evaluation modules.

## Edge Case Inventory

### Source Identity

| Category | Edge Case | Required Behavior |
| --- | --- | --- |
| Missing source | `sourceId` is unknown | Return problem details with 404 semantics. |
| Blank source ID | Empty or whitespace ID | Return problem details with validation semantics. |
| Duplicate source ID | Create request reuses an existing ID | Reject or return the existing idempotent result when an adapter provides idempotency. |
| Unknown fields | Request includes extra fields | Preserve or ignore safely; never fail solely because of unknown optional fields. |
| Unknown source type | Type is not supported in P0 | Return reachable `false`, `connectionStatus = unsupported_type`, and a neutral diagnostic. |

### Organizer Sample Reference

| Category | Edge Case | Required Behavior |
| --- | --- | --- |
| Missing URL | Reference URL omitted for organizer sample | Use the approved default reference and add an informational diagnostic. |
| Non-HTTPS URL | `http`, `file`, `ssh`, `git`, or custom scheme | Mark as `unsafe_reference`; do not connect. |
| URL credentials | Username, password, token, or secret-like value in URL | Mark as `unsafe_reference`; do not echo the secret. |
| Wrong host | Host is not `github.com` | Mark as `unsafe_reference`. |
| Wrong repository | GitHub URL is not `a-klumpp/GDPR-data-samples` | Mark as `unsafe_reference`. |
| Query or fragment | URL contains query or fragment | Mark as `unsafe_reference` to avoid hidden selectors. |
| Redirect or rename | Repository redirects to another location | Future live probe must report degraded until a human approves the new reference. |
| Repository missing | 404 from live probe | Report `not_found` with retryable `false`. |
| GitHub rate limit | 403 or rate-limit headers | Report `rate_limited` with retryable `true`; do not treat as successful. |
| TLS failure | Certificate validation fails | Report `network_error` with retryable `true`; do not bypass TLS. |
| Timeout or DNS failure | Network is unavailable | Report `network_error` with retryable `true`. |
| Directory over 1,000 files | GitHub contents API limit is hit | Future live probe must switch to tree metadata or report degraded. |
| Large files | Individual files exceed API content limits | Connection can remain metadata-only; scan/download must refresh raw content links separately. |
| Symlink or submodule | Root contains non-file entries | Future scan must treat as unsupported until explicitly allowed. |

### Sample Family Metadata

| Category | Edge Case | Required Behavior |
| --- | --- | --- |
| Missing expected family | One of the approved families is absent | Keep source reachable but mark `degraded` and list missing families. |
| Extra family | Unknown family appears | Keep source reachable and add a warning; clients must render neutral state. |
| Duplicate family | Family is repeated | Keep source reachable and warn. |
| Empty family list | No families are available | Mark `degraded`; scanning should not start without operator confirmation. |
| Case drift | Filename or family casing differs | Report degraded; do not normalize silently for evidence labels. |

### Local Sample Source

| Category | Edge Case | Required Behavior |
| --- | --- | --- |
| Missing root path | Local source has no `rootPath` | Return `invalid_config`. |
| Relative path | Path is not absolute | Return `invalid_config`. |
| Missing path | Path does not exist | Return `not_found` with retryable `true`. |
| File instead of directory | Path points to a file | Return `invalid_config`. |
| Unreadable directory | OS read permission is denied | Return `permission_denied`. |
| Escaped root | Path is outside configured allowed roots | Return `policy_denied`. |
| Symlink escape | Path inside allowed root resolves outside allowed root | Return `policy_denied`. |
| Empty directory | Directory has no visible files | Return `degraded` with a warning. |
| Directory listing error | OS raises during listing | Return `permission_denied` or `network_error` according to the exception class. |

### Security and Privacy

| Category | Edge Case | Required Behavior |
| --- | --- | --- |
| Secret in config | Token-like values appear in config | Never include raw secrets in diagnostics or response messages. |
| Raw sample content | Connector can access file contents | Connection test must not return content snippets. |
| Permission mismatch | User lacks a future permission | Return allowed and denied actions when permission boundary is implemented; for now expose capability limits. |
| Automatic deletion | User expects cleanup | Connection test must never delete or mutate source files. |

### Contract and Operations

| Category | Edge Case | Required Behavior |
| --- | --- | --- |
| Partial metadata | Some details are known but source is not fully validated | Set `meta.partial = true` and include warnings. |
| Unknown enum value | Future status appears | Clients must render neutral fallback; server keeps status strings open. |
| Idempotent retry | Same connection test is requested repeatedly | Return a fresh timestamp and trace ID without changing source state. |
| Clock or trace missing | Backend cannot create observability metadata | Return deterministic testable defaults in tests; production adapter must inject clock/trace. |
| Live dependency unavailable | GitHub or filesystem cannot be checked | Return diagnostic status; do not block unrelated UI rendering. |

## Response Extension

`ConnectionTestEnvelope.data` keeps the existing required fields:

- `sourceId`
- `reachable`
- `message`

Optional fields added for diagnostics:

- `connectionStatus`: open string such as `connected`, `degraded`, `invalid_config`, `unsafe_reference`, `policy_denied`, `not_found`, `unsupported_type`, or `network_error`.
- `checkedAt`: ISO 8601 UTC timestamp.
- `capabilities`: metadata about what the connector can do without implying production integration.
- `diagnostics`: ordered diagnostic objects with `code`, `severity`, `message`, and `retryable`.
- `sourceVersion`: optional stable source version such as a commit SHA.
- `contentFingerprint`: optional metadata-only fingerprint; raw content is not exposed.

These fields are optional and additive, so contract version `0.1.0` remains compatible.

## Primitive Acceptance Criteria

| ID | Criterion |
| --- | --- |
| SRC-CONN-001 | A connection test for the default organizer sample source returns `reachable = true`, `connectionStatus = connected`, no raw file content, and metadata-only capabilities. |
| SRC-CONN-002 | An organizer sample source with an unsafe URL returns `reachable = false`, `connectionStatus = unsafe_reference`, and does not attempt remote access. |
| SRC-CONN-003 | Missing expected sample families keep the source reachable but return `connectionStatus = degraded`, `meta.partial = true`, and warnings. |
| SRC-CONN-004 | A local sample source outside allowed roots or escaping through symlinks returns `connectionStatus = policy_denied`. |
| SRC-CONN-005 | Unknown source IDs return RFC 9457-compatible problem details. |
| SRC-CONN-006 | Unsupported source types return a neutral unreachable result, not a crash. |
| SRC-CONN-007 | Connection test responses preserve the existing envelope shape and required fields from `contracts/openapi.yaml`. |
| SRC-CONN-008 | Behavior tests cover success, degraded metadata, invalid config, unsafe reference, local boundary denial, missing source, and unsupported source cases. |

## Impact Surface

- Backend source connection core.
- `contracts/schemas/source-scan.yaml` optional diagnostics fields.
- `contracts/mocks/sources.json` source metadata.
- `docs/API_CONTRACT.md`, `docs/PRD.md`, `docs/TRD.md`, `docs/DesignSpec.md`, `docs/TestCase.md`, and `ACCEPTANCE.md`.

