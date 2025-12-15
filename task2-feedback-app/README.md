# Task 2 – Two-Dashboard AI Feedback System

FastAPI + SQLite + Jinja templates. One shared datastore drives both dashboards.

## Quickstart (local)
```bash
cd task2-feedback-app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# env (OpenRouter; falls back to stub if absent)
export OPENROUTER_API_KEY=your_key_here
export OPENROUTER_MODEL=mistralai/mistral-7b-instruct  # choose a valid OpenRouter model ID
export USE_JSON_FORMAT=true
export OPENROUTER_REFERRER=https://localhost
export OPENROUTER_APP=fynd-feedback-app

uvicorn app.main:app --reload --port 8000
```
Open `http://localhost:8000` for the user dashboard and `http://localhost:8000/admin` for the admin dashboard.

## Deployment (Docker-based, Vercel/Render/Fly)
- Uses `Dockerfile`. Set envs:\
  `OPENROUTER_API_KEY` (required), `OPENROUTER_MODEL` (default mistralai/mistral-7b-instruct), `USE_JSON_FORMAT` (true/false), `OPENROUTER_REFERRER`, `OPENROUTER_APP`, `DATABASE_URL` (for managed DB, e.g., Postgres URL).
- Build/run: `docker build -t feedback-app .` then `docker run -p 8000:8000 --env-file .env feedback-app`
- On Vercel: choose “Use Dockerfile” and add the env vars above. Use a managed DB (e.g., Supabase Postgres) via `DATABASE_URL`; do not rely on local SQLite in serverless.
- On Render/Fly: deploy the Docker image or point to this repo; set the same env vars. Persist data via managed DB or volume.

## Features
- User dashboard: rate 1–5, submit review, receive AI response; data persisted.
- Admin dashboard: live-updating table (polls `/admin/data`), shows rating, review, AI summary, AI actions; analytics (count, avg rating).
- Shared datastore: SQLite via SQLAlchemy.
- LLM: OpenRouter-compatible chat API; graceful fallback if no key configured.

## Notes
- Adjust polling in `templates/admin.html` if needed.
- To change model/provider, edit `call_llm` in `app/main.py`.
