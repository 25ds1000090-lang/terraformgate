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


def is_exact_bool(value: object) -> bool:
    return type(value) is bool


def valid_shape(body: object) -> bool:
    if not isinstance(body, dict):
        return False
    if not {"environment", "state", "providerVersion", "destroyApproved", "resource"}.issubset(body):
        return False
    if not isinstance(body["environment"], str) or not isinstance(body["providerVersion"], str):
        return False
    if not is_exact_bool(body["destroyApproved"]):
        return False
    state = body["state"]
    if not isinstance(state, dict) or not {"backend", "locked"}.issubset(state):
        return False
    if not isinstance(state["backend"], str) or not is_exact_bool(state["locked"]):
        return False
    resource = body["resource"]
    fields = {"address", "type", "action", "labels", "secret", "forceDestroy"}
    if not isinstance(resource, dict) or not fields.issubset(resource):
        return False
    if not all(isinstance(resource[key], str) for key in ("address", "type", "action")):
        return False
    if resource["action"] not in VALID_ACTIONS or not isinstance(resource["labels"], dict):
        return False
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in resource["labels"].items()):
        return False
    if resource["secret"] is not None and not isinstance(resource["secret"], str):
        return False
    return is_exact_bool(resource["forceDestroy"])


def evaluate(body: object) -> tuple[str, str]:
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
    if any(resource["labels"].get(k) != v for k, v in REQUIRED_LABELS.items()):
        return "reject", "MISSING_LABELS"
    secret = resource["secret"]
    if secret is not None and not (secret.startswith("secret://") and len(secret) > 9):
        return "reject", "PLAINTEXT_SECRET"
    if (resource["action"] == "delete" and resource["type"] in STATEFUL_TYPES
            and body["destroyApproved"] is not True):
        return "reject", "DELETE_NOT_APPROVED"
    if resource["type"] == "storage_bucket" and resource["forceDestroy"] is True:
        return "reject", "FORCE_DESTROY"
    return "approve", "APPROVE"
