# Contracts

This folder contains the frontend-backend delivery contract.

- `openapi.yaml` is the machine-readable API source of truth.
- `schemas/` keeps schema files split below the repository file-size guardrail.
- `mocks/` contains contract fixtures for frontend work before backend endpoints exist.
- Governance mocks cover active policy packs, permission boundaries, and reviewer support.
- `mocks/connectionTest.json` shows the additive diagnostics shape for `POST /sources/{sourceId}/connect-test`.
- `mocks/sourceConnectionScenarios.json` contains source connection success, degraded, unsafe, unsupported, and problem-response scenarios for frontend and QA work.
- `mocks/sourceConnectionProbeScenarios.json` contains deterministic external probe simulations such as timeout, TLS failure, rate limit, remote not found, redirect, and invalid probe config.

Contract version: `0.1.0`.

Compatibility rule: additive optional response fields are allowed; breaking changes require a version bump and updates to `docs/API_CONTRACT.md`.
