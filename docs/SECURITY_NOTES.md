# Security and Privacy Notes

## P0 Safety Boundary

The hackathon prototype must simulate deletion. It must not delete, quarantine, alter, or remotely move real user files.

## Sensitive Data Handling

- Mock snippets must be redacted.
- Evidence examples must not contain real personal data.
- UI examples should show masked values, such as `[REDACTED]` or `DE** ****`.
- Raw extracted text is not part of the public API contract.
- Audit examples should include decision metadata, not raw sensitive content.

## Role Simulation

P0 may simulate roles with `X-Actor-Id`. This is not authentication. Production authentication and authorization are deferred.

## Permission Boundary UX

P0 should expose allowed and denied actions to the UI. This improves user control without pretending that role simulation is production authorization.

## External Services

P0 must not require live Microsoft Graph, production OAuth, tenant secrets, paid AI services, or external deletion APIs.

## Source Connection Safety

- Connection tests must be side-effect-free.
- Organizer sample references must use the approved HTTPS GitHub repository URL without credentials, query strings, or fragments.
- Local sample sources must resolve inside explicitly configured allowed roots.
- Diagnostics must not echo tokens, passwords, raw sample content, or unredacted sensitive values.

## Review Safety

Any future production deletion path must include:

- Human approval.
- Retention check.
- Legal hold check.
- Audit event.
- Rollback or recovery story.
- Explicit design note before implementation.

## Law-Agnostic Structure

Scanner and review workflow code should consume policy-pack guidance. It should not hard-code one current legal interpretation as permanent structure.
