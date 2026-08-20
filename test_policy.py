from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

VALID = {
    "environment": "prod-y29t9r",
    "state": {"backend": "gcs", "locked": True},
    "providerVersion": "~> 6.0",
    "destroyApproved": False,
    "resource": {
        "address": "google_storage_bucket.data",
        "type": "storage_bucket",
        "action": "create",
        "labels": {
            "owner": "student-r8bq2",
            "environment": "production",
            "cost_center": "cc-3i81",
        },
        "secret": None,
        "forceDestroy": False,
    },
}


def test_valid_plan():
    response = client.post("/terraform/plan", json=VALID)
    assert response.status_code == 200
    assert response.json() == {"decision": "approve", "reason": "APPROVE"}
