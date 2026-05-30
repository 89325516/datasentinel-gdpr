# Design Specification

## Design Goal

The future product experience should make GDPR data cleanup feel like an accountable review workflow, not an automatic deletion tool.

## Conceptual Workflow State Machine

| State | Event | Guard | Next State | Side Effect |
| --- | --- | --- | --- | --- |
| Source registered | Connection test requested | Source exists and metadata is valid | Source connected | Return capability and diagnostic metadata |
| Source registered | Connection test requested | Source exists but metadata is incomplete | Source degraded | Return warning diagnostics |
| Source registered | Connection test requested | Source is unknown or unsafe | Source rejected | Return problem details or unreachable diagnostics |
| Source selected | Full scan requested | Source is readable | Scanning | Record scan start |
| Scanning | File analyzed | File can be parsed | Finding classified | Store finding evidence |
| Scanning | File cannot be parsed | Error is recoverable | Needs review | Record extraction issue |
| Finding classified | Owner resolved | Owner confidence is sufficient | Assigned | Notify or queue owner |
| Finding classified | Owner unresolved | No reliable owner | Escalated | Queue for privacy team |
| Assigned | Reviewer decides delete | Reviewer is authorized | Delete approved | Record decision and reason |
| Assigned | Reviewer decides retain | Reviewer gives reason | Retain approved | Record exception |
| Assigned | Reviewer escalates | Escalation target exists | Escalated | Record escalation |
| Delete approved | Deletion executed | Deletion is supported | Closed | Record deletion result |
| Delete approved | Deletion fails | Failure is recoverable | Needs review | Record failure |
| Closed | Delta scan requested | Previous scan baseline exists | Scanning changes | Compare changed files only |

## Experience Principles

- Show evidence, not hidden model conclusions.
- Mask sensitive snippets by default.
- Keep every decision attributable to a human or system actor.
- Make deletion, retention, and escalation reasons visible in the audit trail.
- Separate risk explanation from legal conclusion.
- Show scan quality metrics as first-class product evidence.
- Render partial data gracefully when the API reports `meta.partial = true`.
- Give users a clear sense of their permission boundary before they act.
- Make reviewer guidance operational through checklists, available decisions, transfer options, and escalation options.

## P0 Information Architecture

| Surface | Purpose |
| --- | --- |
| Source Connector | Select a controlled demo source and start full or delta scans. |
| Source Connection Diagnostics | Show reachability, degraded state, capability limits, and retryable errors before scan start. |
| Admin Dashboard | Show official KPIs, scan progress, review backlog, and risk distribution. |
| Findings Table | Show risk-ranked findings filtered by owner, scan, status, or risk level. |
| Evidence Card | Show redacted evidence, signals, context, owner, retention status, and audit timeline. |
| Review Panel | Let a human record a decision with a reason. |
| Audit View | Show scan and review events. |
| Evaluation Tab | Show accuracy, reproducibility, speed, and resource intensity. |
| Governance Settings | Show active policy pack, organization model, source adapters, and change controls. |
| Permission Boundary | Show allowed actions, denied actions, visible scopes, and denial reasons. |

## Reviewer-Friendly Requirements

- Show a plain-language summary before every decision.
- Show why an action is allowed or denied.
- Show required reason fields before submit.
- Provide transfer and escalation options when ownership is unclear.
- Keep legal conclusions out of UI copy; show policy guidance and human decision requirements.

## Deferred Design Decisions

- Visual design system.
- Interaction details.
- Framework-specific components.
- Data persistence model.
