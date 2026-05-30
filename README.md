# DataSentinel GDPR

DataSentinel GDPR is a hackathon project concept for GDPR-relevant data discovery and accountable cleanup workflows.

The project goal is to help an organization identify, classify, route, review, and audit personal-data findings across distributed file sources such as OneDrive, SharePoint, shared drives, and local sample repositories.

This repository is currently initialized for planning, collaboration, contract-first delivery, and the first backend source-connection vertical slice. It does not contain production integration code yet.

## Product Thesis

Find risky personal-data records, explain why they matter, route them to the accountable human, and prove what happened.

## Current Scope

- Maintain English-language project documentation.
- Keep acceptance criteria explicit and reviewable.
- Prepare the repository for collaborative implementation.
- Define a tolerant frontend-backend contract for parallel delivery.
- Implement a metadata-only backend source connection core for controlled sample and mock sources.
- Avoid speculative architecture, dependencies, or product features before they are accepted.

## Source Connection Mock Server

Run the local backend mock for the source connector contract:

```bash
python3 -m backend.datasentinel.source_server --host 127.0.0.1 --port 8000
```

This server exposes the source connection routes for frontend contract testing. It is not a production runtime.

## Non-Goals

- No automatic deletion of user data without human review.
- No legal advice.
- No production integration with Microsoft 365 or other external systems yet.
- No production implementation code before project requirements and technical approach are approved.

## Documents

- [Project Context](docs/PROJECT_CONTEXT.md)
- [Business Requirements](docs/BRD.md)
- [Market Requirements](docs/MRD.md)
- [Product Requirements](docs/PRD.md)
- [Technical Requirements](docs/TRD.md)
- [Design Specification](docs/DesignSpec.md)
- [Test Cases](docs/TestCase.md)
- [API Contract](docs/API_CONTRACT.md)
- [Parallel Delivery Workflow](docs/DELIVERY_WORKFLOW.md)
- [Evaluation Harness](docs/EVALUATION.md)
- [Security Notes](docs/SECURITY_NOTES.md)
- [Demo Script](docs/DEMO_SCRIPT.md)
- [Governance Configuration](docs/GOVERNANCE_CONFIG.md)
- [Organizer Sample References](docs/GDPR_SAMPLE_REFERENCES.md)
- [Sample Source Connection Design](docs/design/sample-source-connection.md)
- [Source Connection Frontend Contract](docs/SOURCE_CONNECTION_FRONTEND_CONTRACT.md)
- [Acceptance Criteria](ACCEPTANCE.md)

## Frontend-Backend Contract

- Machine-readable API contract: [contracts/openapi.yaml](contracts/openapi.yaml)
- Contract schemas: [contracts/schemas](contracts/schemas)
- Mock payloads: [contracts/mocks](contracts/mocks)
- AI agent instructions: [AGENTS.md](AGENTS.md)

## Collaboration

All repository content, issues, pull requests, commit messages, and documentation should be written in English.
