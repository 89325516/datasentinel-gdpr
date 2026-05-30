# Organizer Sample References

## Source

The organizer sample repository is `a-klumpp/GDPR-data-samples`:

https://github.com/a-klumpp/GDPR-data-samples

The repository is public and contains PDF sample families for:

- `Expense_Report`
- `IT_Access_Request`
- `Incident_Report`
- `Supplier_Onboarding`
- `Training_Evaluation`

These names were verified from the public GitHub repository listing on 2026-05-30.

The `main` branch reference observed for the metadata-only backend seed on 2026-05-30 was:

```text
76b0f66d5594d7fccfdd103c8379f7d9d7356aeb
```

## Contract Usage

The sample repository is represented as a mock source in `contracts/mocks/sources.json` with `sourceType = organizer_sample_repo`.

Frontend use:

- Show it as the default demo source.
- Let users start a full scan from this source in mock mode.
- Show sample families as source metadata.

Backend use:

- Start with metadata-only source registration.
- Test the sample source connection through diagnostics and capabilities before scan start.
- Do not copy PDFs into this repository unless licensing and storage choices are reviewed.
- If a backend later downloads samples for local tests, keep that behind an explicit script and document the source URL.

Evaluation use:

- Use sample families as controlled categories for scanner behavior.
- Store labels separately from downloaded files.
- Keep policy-pack version and dataset hash in evaluation output.

## Boundary

This repository does not vendor the organizer PDFs. It references the public source and keeps contract fixtures small.
