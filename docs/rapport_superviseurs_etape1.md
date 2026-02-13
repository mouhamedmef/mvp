# Rapport - Etape 1 MVP (Support L1 IA)

## 1. Contexte
Le projet vise a automatiser le support client niveau 1 (L1) pour des startups SaaS, afin de reduire les couts et liberer les equipes humaines pour les cas L2/L3.

## 2. Objectif de cette etape
Objectif de l'etape 1: valider un flux minimum de bout en bout.

Flux valide:
1. Un utilisateur envoie un message.
2. Le message passe par un noeud LangGraph.
3. Le systeme renvoie une reponse.
4. La conversation est enregistree en base PostgreSQL.

## 3. Realisations effectuees
### 3.1 Backend API (FastAPI)
Un backend Python a ete mis en place avec endpoints de base:
- `GET /health` pour verifier que le service repond.
- `GET /v1/models` pour exposer le modele local `echo-langgraph`.
- `POST /v1/chat/completions` compatible OpenAI-like pour l'integration chat.
- `GET /v1/logs` pour consulter les derniers echanges enregistres.

### 3.2 Orchestration (LangGraph)
Un graphe minimal a ete cree avec un noeud `echo`:
- entree: `user_input`
- sortie: `bot_output`

Dans cette etape, la sortie est volontairement simple (echo de l'entree) pour valider l'architecture avant ajout d'intelligence metier.

### 3.3 Base de donnees (PostgreSQL via Docker)
Une base PostgreSQL est lancee avec Docker Compose.
- creation automatique de la table `chat_logs` au demarrage backend.
- insertion automatique de chaque interaction (message utilisateur + reponse assistant).

### 3.4 Securite minimale (API key)
Un middleware verifie la presence d'un token `Bearer` sur les routes `/v1/*`.
Cela permet un premier niveau de controle d'acces pour les tests d'integration.

### 3.5 Interface de test simplifiee (Streamlit)
En plus de LibreChat, une interface Streamlit a ete ajoutee pour accelerer les tests:
- saisie d'un message
- appel de l'API backend
- affichage de la reponse

Cette interface est plus simple pour un demarrage rapide.

## 4. Architecture actuelle
1. Frontend de test (Streamlit ou LibreChat)
2. API FastAPI (`/v1/chat/completions`)
3. LangGraph (noeud `echo`)
4. Persistance PostgreSQL (`chat_logs`)

## 5. Livrables produits
- `backend/app/graph.py`
- `backend/app/main.py`
- `backend/app/db.py`
- `backend/requirements.txt`
- `docker-compose.yml`
- `frontend_streamlit/app.py`
- `README.md`

## 6. Tests et validation
Validation effectuee:
- verification de syntaxe Python (`compileall`).
- tests API manuels via PowerShell (`/health`, `/v1/chat/completions`, `/v1/logs`).
- verification du flux complet depuis UI Streamlit.

Incident rencontre:
- erreur `ModuleNotFoundError: No module named 'psycopg'`
Cause:
- environnement Python non aligne avec les dependances du projet.
Resolution:
- activation du venv `.venv` + installation `pip install -r backend/requirements.txt` + execution via `python -m uvicorn`.

## 7. Limites de l'etape 1
- Le bot est un echo (pas encore de logique metier L1 reelle).
- Pas encore de classification automatique, base de connaissances, ni escalade L2/L3.
- Pas encore de systeme de monitoring complet (metrics, dashboards).

## 8. Prochaines etapes proposees
1. Ajouter une base de connaissances (FAQ/doc interne).
2. Remplacer le noeud echo par un noeud de reponse contextuelle.
3. Ajouter routage de tickets: resolu L1 vs escalade L2/L3.
4. Ajouter evaluation qualite (precision, taux de resolution, temps de reponse).
5. Ajouter logs structures et observabilite.

## 9. Conclusion
Cette etape valide le socle technique du MVP:
- pipeline conversationnel operationnel
- orchestration LangGraph integree
- persistence PostgreSQL active
- endpoint compatible integration chat

Le projet est maintenant pret pour la phase suivante: passer d'un flux technique valide a une vraie automatisation L1 basee IA.
