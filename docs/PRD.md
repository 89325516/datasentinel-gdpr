# Product Requirements Document

## Product Goal

Provide a prototype workflow that shows how an organization can discover GDPR-relevant data, classify risk, assign ownership, support human review, and prove the outcome.

## Initial User Journey

1. A privacy or IT user starts with a controlled sample file source.
2. The system identifies candidate files that may contain personal or GDPR-relevant data.
3. The system explains why each finding matters.
4. The system suggests an accountable owner or escalation path.
5. A human reviewer decides whether to delete, retain, mask, archive, or escalate the finding.
6. The system records the decision in an audit trail.
7. A later delta scan focuses only on new or changed files.

## Required Capabilities

- Full-scan concept for initial discovery.
- Source-connection validation for controlled sample and mock sources before scans start.
- Classification concept for personal-data findings and risk context.
- Owner-routing concept for review accountability.
- Human-review concept with decision reasons.
- Audit-log concept for evidence and outcomes.
- Delta-scan concept for ongoing governance.
- Admin-reporting concept for scanned files, flagged files, scanned volume, progress, scan time, backlog, and risk distribution.
- Evaluation concept for accuracy, reproducibility, speed, and resource intensity.
- Governance-configuration concept for policy packs, organization model, permissions, review support, and change previews.
- User-control concept for visible allowed actions, denied actions, and reason requirements.

## P0 Screens and API Consumers

- Source connector view.
- Admin dashboard.
- Findings table.
- Evidence card.
- Review action panel.
- Audit timeline or report view.
- Evaluation tab.
- Governance settings inspection.
- Permission boundary view.

These surfaces must consume the tolerant contract defined in `docs/API_CONTRACT.md` and `contracts/openapi.yaml`.

## Explicitly Deferred

- Production Microsoft 365 integration.
- Real deletion of remote files.
- Authentication and authorization implementation.
- Persistent storage selection.
- AI model or vendor selection.
- User interface implementation.

## Product Constraints

- User-facing and repository text must be English.
- Deletion must be human-accountable.
- Sensitive snippets should be minimized or masked in any future UI.
- Source connection results must expose reachability, degraded states, capability limits, and diagnostics without exposing secrets or raw source content.
- Frontend and backend work must use the shared API contract and mock fixtures.
- Legal rules must be represented as configurable guidance, not fixed code conclusions.
- User interfaces must show permission boundaries and avoid surprising denial after submit.
- Requirements changes must update this document and `ACCEPTANCE.md`.
