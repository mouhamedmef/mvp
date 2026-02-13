# Documentation Technique - Code Etape 1

## 1. Vue d'ensemble
Stack:
- Backend: Python 3.12 + FastAPI
- Orchestrateur: LangGraph
- Base de donnees: PostgreSQL (Docker)
- UI test rapide: Streamlit

Objectif technique:
- Exposer une API chat compatible OpenAI-like.
- Passer le message utilisateur dans LangGraph.
- Retourner une reponse assistant.
- Sauvegarder les echanges en base.

## 2. Arborescence utile
- `backend/app/main.py`: API, auth, endpoints, streaming.
- `backend/app/graph.py`: definition du graphe LangGraph.
- `backend/app/db.py`: acces DB et CRUD des logs.
- `frontend_streamlit/app.py`: UI de test locale.
- `docker-compose.yml`: service PostgreSQL.
- `backend/requirements.txt`: dependances Python.

## 3. Details module par module

### 3.1 `backend/app/graph.py`
Responsabilite:
- Definir l'etat de conversation `ChatState`.
- Declarer le noeud `echo_node`.
- Construire et compiler le graphe.

Comportement:
- Recoit `user_input`.
- Retourne `bot_output = user_input`.

### 3.2 `backend/app/db.py`
Responsabilite:
- Lire la variable `DATABASE_URL`.
- Initialiser la table `chat_logs`.
- Inserer et lire les logs.

Fonctions principales:
- `get_database_url()`
- `init_db()`
- `insert_chat_log(model, user_message, assistant_message)`
- `fetch_recent_logs(limit=20)`

Schema SQL cree automatiquement:
```sql
CREATE TABLE IF NOT EXISTS chat_logs (
  id BIGSERIAL PRIMARY KEY,
  model TEXT NOT NULL,
  user_message TEXT NOT NULL,
  assistant_message TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.3 `backend/app/main.py`
Responsabilite:
- Configurer FastAPI + CORS.
- Initialiser la DB au demarrage.
- Verifier l'API key sur routes `/v1/*`.
- Exposer les endpoints API.
- Appeler LangGraph puis logger en DB.

Endpoints:
- `GET /health`: statut service.
- `GET /v1/models`: liste des modeles exposes.
- `GET /v1/logs?limit=...`: recupere les derniers logs.
- `POST /v1/chat/completions`: endpoint principal chat.

Auth:
- Header requis: `Authorization: Bearer <API_KEY>`
- Variable d'env: `API_KEY` (defaut local: `pfe-local-key`).

Streaming:
- Support `stream=true` via `text/event-stream`.
- Retour chunk par chunk + `[DONE]`.

Flux interne de `POST /v1/chat/completions`:
1. Extraire le dernier message `role=user`.
2. Appeler `graph.invoke({"user_input": ...})`.
3. Inserer en base via `insert_chat_log(...)`.
4. Retourner JSON standard ou flux streaming.

### 3.4 `frontend_streamlit/app.py`
Responsabilite:
- Fournir une interface de test locale simple.
- Envoyer un message au backend.
- Afficher reponse assistant.

Parametres configurables (sidebar):
- URL backend
- modele
- API key
- timeout

## 4. Contrat API (resume)

### 4.1 Request `POST /v1/chat/completions`
```json
{
  "model": "echo-langgraph",
  "messages": [
    {"role": "user", "content": "bonjour"}
  ],
  "stream": false
}
```

### 4.2 Headers
```http
Authorization: Bearer pfe-local-key
Content-Type: application/json
```

### 4.3 Response (non-stream)
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "echo-langgraph",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "bonjour"},
      "finish_reason": "stop"
    }
  ],
  "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
}
```

## 5. Variables d'environnement
- `API_KEY`: cle de securite des endpoints `/v1/*`.
- `DATABASE_URL`: URL de connexion PostgreSQL.

Exemple:
```powershell
$env:API_KEY="pfe-local-key"
$env:DATABASE_URL="postgresql://support_user:support_pass@localhost:5432/support_ai"
```

## 6. Execution locale (resume)
1. `docker compose up -d postgres`
2. `py -3.12 -m venv .venv`
3. `\.venv\Scripts\Activate.ps1`
4. `pip install -r backend\requirements.txt`
5. Set env vars `API_KEY`, `DATABASE_URL`
6. `python -m uvicorn app.main:app --reload --app-dir backend --port 8000`
7. (optionnel) `streamlit run frontend_streamlit\app.py`

## 7. Troubleshooting rapide
- `ModuleNotFoundError: psycopg`
Action: activer venv puis reinstaller requirements.

- `401 Unauthorized`
Action: verifier header `Authorization: Bearer ...` et valeur `API_KEY`.

- erreur DB connexion
Action: verifier Docker Desktop, container Postgres, `DATABASE_URL`.

## 8. Prochaine evolution technique
- Integrer vraie logique L1 (FAQ/KB retrieval).
- Ajouter classification intention et fallback escalade.
- Ajouter tests unitaires + integration.
- Ajouter observabilite (logs structures, latence, taux resolution).
