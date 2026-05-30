from __future__ import annotations

from typing import Any


CONTRACT_VERSION = "0.1.0"
ORGANIZER_SOURCE_ID = "source_001"
ORGANIZER_REFERENCE_URL = "https://github.com/a-klumpp/GDPR-data-samples"
ORGANIZER_REPO_VERSION = "76b0f66d5594d7fccfdd103c8379f7d9d7356aeb"
EXPECTED_SAMPLE_FAMILIES = (
    "Expense_Report",
    "IT_Access_Request",
    "Incident_Report",
    "Supplier_Onboarding",
    "Training_Evaluation",
)


def default_sources() -> list[dict[str, Any]]:
    return [
        {
            "sourceId": ORGANIZER_SOURCE_ID,
            "name": "Organizer GDPR Data Samples",
            "sourceType": "organizer_sample_repo",
            "status": "mock_ready",
            "rootLabel": "a-klumpp/GDPR-data-samples",
            "masterOfDataUserId": "user_anna",
            "referenceUrl": ORGANIZER_REFERENCE_URL,
            "sourceVersion": ORGANIZER_REPO_VERSION,
            "sampleFamilies": list(EXPECTED_SAMPLE_FAMILIES),
        },
        {
            "sourceId": "source_002",
            "name": "Mock SharePoint Finance",
            "sourceType": "sharepoint_mock",
            "status": "mocked",
            "rootLabel": "SharePoint Finance",
            "masterOfDataUserId": "user_anna",
        },
    ]

