# Terraform Plan Policy Gate

FastAPI endpoint for the normalized Terraform plan policy assignment.

## Endpoint

`POST /terraform/plan`

## Run locally

```bash
python -m pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Deploy on Render

1. Upload this folder to a GitHub repository.
2. In Render, create a **Web Service** from that repository.
3. Use `pip install -r requirements.txt` as the build command.
4. Use `uvicorn app:app --host 0.0.0.0 --port $PORT` as the start command.
5. After deployment, test the exact HTTPS URL with `/terraform/plan`.
6. Submit only the base URL, for example `https://terraform-plan-policy-gate.onrender.com`.

Do not add a trailing endpoint path, query string, credentials, or fragment to the submitted base URL.
