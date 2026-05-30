# Business Requirements Document

## Goal

Create a GDPR data discovery and cleanup control-tower prototype that helps organizations find personal data, understand risk, assign accountability, and record human review decisions.

## Business Problem

Organizations often store personal and GDPR-relevant data across fragmented file systems. Manual discovery and review become impractical when files are distributed across personal drives, shared drives, and collaboration platforms.

## Business Outcomes

- Improve visibility into where personal data may exist.
- Prioritize risky or potentially overdue files for review.
- Route findings to accountable owners.
- Preserve an audit trail for deletion, retention, escalation, or exception decisions.
- Support future full-scan and delta-scan governance loops.
- Validate controlled sample source connections with explicit diagnostics before scan work begins.
- Report measurable scanning quality through accuracy, reproducibility, speed, and resource intensity.
- Adapt to policy changes, organization changes, ownership transfers, and reviewer delegation without code rewrites.
- Give users clear visibility into their permissions and decision boundaries.

## Constraints

- The system must not blindly delete data.
- Human accountability is required for deletion or retention decisions.
- This project does not provide legal advice.
- This repository must remain English-only.
- No production integrations are approved at initialization time.
- Policy details must be configurable guidance, not fixed legal conclusions.

## Done When

The team has a reviewed prototype scope, accepted criteria, a tolerant frontend-backend delivery contract, and a technical plan before implementation begins.
