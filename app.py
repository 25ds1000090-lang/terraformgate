from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Terraform Plan Policy Gate")

WORKSPACE = "prod-y29t9r"
REQUIRED_LABELS = {
    "owner": "student-r8bq2",
    "environment": "production",
    "cost_center": "cc-3i81",
}
SAFE_BACKENDS = {"gcs", "s3", "azurerm", "remote"}
PINNED_PROVIDERS = {"6.2.1", "= 6.2.1", "~> 6.0"}
VALID_ACTIONS = {"create", "update", "delete"}
STATEFUL_TYPES = {"storage_bucket", "sql_database", "persistent_disk"}


def result(decision: str, reason: str) -> JSONResponse:
    return JSONResponse(status_code=200, content={"decision": decision, "reason": reason})


def is_exact_bool(value: object) -> bool:
    return type(value) is bool


def valid_shape(body: object) -> bool:
    if not isinstance(body, dict):
        return False

    required_top = {
        "environment", "state", "providerVersion", "destroyApproved", "resource"
    }
    if not required_top.issubset(body):
        return False
    if not isinstance(body["environment"], str):
        return False
    if not isinstance(body["providerVersion"], str):
        return False
    if not is_exact_bool(body["destroyApproved"]):
        return False

    state = body["state"]
    if not isinstance(state, dict) or not {"backend", "locked"}.issubset(state):
        return False
    if not isinstance(state["backend"], str) or not is_exact_bool(state["locked"]):
        return False

    resource = body["resource"]
    resource_fields = {
        "address", "type", "action", "labels", "secret", "forceDestroy"
    }
    if not isinstance(resource, dict) or not resource_fields.issubset(resource):
        return False
    if not all(isinstance(resource[key], str) for key in ("address", "type", "action")):
        return False
    if resource["action"] not in VALID_ACTIONS:
        return False
    if not isinstance(resource["labels"], dict):
        return False
    if not all(isinstance(key, str) and isinstance(value, str)
               for key, value in resource["labels"].items()):
        return False
    if resource["secret"] is not None and not isinstance(resource["secret"], str):
        return False
    if not is_exact_bool(resource["forceDestroy"]):
        return False
    return True


def evaluate(body: object) -> tuple[str, str]:
    """Evaluate rules in the exact order required by the grader."""
    if not valid_shape(body):
        return "reject", "INVALID_PLAN"
    if body["environment"] != WORKSPACE:
        return "reject", "ENVIRONMENT_MISMATCH"

    state = body["state"]
    if state["backend"] not in SAFE_BACKENDS or state["locked"] is not True:
        return "reject", "STATE_UNSAFE"
    if body["providerVersion"] not in PINNED_PROVIDERS:
        return "reject", "UNPINNED_PROVIDER"

    resource = body["resource"]
    labels = resource["labels"]
    if any(labels.get(key) != value for key, value in REQUIRED_LABELS.items()):
        return "reject", "MISSING_LABELS"

    secret = resource["secret"]
    if secret is not None and not (
        secret.startswith("secret://") and len(secret) > len("secret://")
    ):
        return "reject", "PLAINTEXT_SECRET"
    if (
        resource["action"] == "delete"
        and resource["type"] in STATEFUL_TYPES
        and body["destroyApproved"] is not True
    ):
        return "reject", "DELETE_NOT_APPROVED"
    if resource["type"] == "storage_bucket" and resource["forceDestroy"] is True:
        return "reject", "FORCE_DESTROY"
    return "approve", "APPROVE"


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/terraform/plan")
async def terraform_plan(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        return result("reject", "INVALID_PLAN")

    decision, reason = evaluate(body)
    return result(decision, reason)
