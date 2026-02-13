# PFE MVP - Step 1 (Echo Support Bot)

This project currently does:
1. Receive a user message.
2. Pass it through a LangGraph node.
3. Return the same message (echo).
4. Save user/assistant messages to PostgreSQL.

## Prerequisites
- Python `3.12.x`
- Docker Desktop running
- PowerShell terminal (Windows)

## Project Structure
- Backend API: `backend/app/main.py`
- LangGraph flow: `backend/app/graph.py`
- PostgreSQL compose: `docker-compose.yml`
- Simple UI (beginner-friendly): `frontend_streamlit/app.py`

## Run The Project (Local PC)

### 1) Start PostgreSQL
Open **Terminal 1** in `c:\Users\HP\Desktop\pfe code`:

```powershell
docker compose up -d postgres
docker compose ps
```

Expected: `pfe_postgres` is `healthy`.

### 2) Install Python dependencies
Open **Terminal 2** in the same folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

### 3) Set backend environment variables
In **Terminal 2**:

```powershell
$env:API_KEY = "pfe-local-key"
$env:DATABASE_URL = "postgresql://support_user:support_pass@localhost:5432/support_ai"
```

### 4) Run backend API
In **Terminal 2**:

```powershell
uvicorn app.main:app --reload --app-dir backend --port 8000
```

Backend will be available at `http://localhost:8000`.

### 5) Quick backend test (recommended)
Open **Terminal 3**:

```powershell
$headers = @{ Authorization = "Bearer pfe-local-key" }
$body = @{
  model = "echo-langgraph"
  messages = @(
    @{ role = "user"; content = "hello" }
  )
  stream = $false
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method POST -Uri "http://localhost:8000/v1/chat/completions" -Headers $headers -ContentType "application/json" -Body $body
```

Expected assistant content: `hello`.

### 6) Run simple chat UI (Streamlit)
In **Terminal 3**:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run frontend_streamlit\app.py
```

Open: `http://localhost:8501`

Default UI values:
- Backend URL: `http://localhost:8000/v1/chat/completions`
- API Key: `pfe-local-key`
- Model: `echo-langgraph`

## Check Saved Logs In PostgreSQL (via API)

```powershell
$headers = @{ Authorization = "Bearer pfe-local-key" }
Invoke-RestMethod -Method GET -Uri "http://localhost:8000/v1/logs?limit=10" -Headers $headers
```

Delete one saved conversation row:

```powershell
$headers = @{ Authorization = "Bearer pfe-local-key" }
Invoke-RestMethod -Method DELETE -Uri "http://localhost:8000/v1/logs/1" -Headers $headers
```

## Optional: Connect LibreChat
Use this in LibreChat `librechat.yaml`:

```yaml
endpoints:
  custom:
    - name: "pfe-echo"
      apiKey: "${PFE_API_KEY}"
      baseURL: "http://host.docker.internal:8000/v1"
      models:
        default: ["echo-langgraph"]
        fetch: false
      titleConvo: false
      summarize: false
      forcePrompt: false
```

In LibreChat `.env`:

```env
PFE_API_KEY=pfe-local-key
```

`baseURL` rule:
- LibreChat in Docker: `http://host.docker.internal:8000/v1`
- LibreChat on host PC: `http://localhost:8000/v1`

## Common Issues
- `401 Unauthorized`: wrong/missing `Bearer` API key.
- DB connection error: check Docker is running and `pfe_postgres` is healthy.
- `ModuleNotFoundError`: activate `.venv` and run `pip install -r backend\requirements.txt`.

## Project Docs
- Supervisor report: `docs/rapport_superviseurs_etape1.md`
- Code documentation: `docs/documentation_code_etape1.md`
