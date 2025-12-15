# Task 2 – Two-Dashboard AI Feedback System

FastAPI + SQLite + Jinja templates. One shared datastore drives both dashboards.

## Quickstart (local)
```bash
cd task2-feedback-app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# env (OpenRouter; falls back to stub if absent for local only)
export OPENROUTER_API_KEY=your_key_here
export OPENROUTER_MODEL=mistralai/mistral-7b-instruct  # choose a valid OpenRouter model ID
export USE_JSON_FORMAT=true
export OPENROUTER_REFERRER=https://localhost
export OPENROUTER_APP=fynd-feedback-app
# required in production (Vercel): managed Postgres URL, e.g. from Supabase/Neon
export DATABASE_URL=postgres://USER:PASSWORD@HOST:PORT/DB

uvicorn app.main:app --reload --port 8000
```
Open `http://localhost:8000` for the user dashboard and `http://localhost:8000/admin` for the admin dashboard.

## Deployment (Vercel serverless)
- Root directory: `task2-feedback-app`
- Framework preset: Other; no build/output commands needed
- Env vars (required): `DATABASE_URL` (managed Postgres URI), `OPENROUTER_API_KEY`
- Env vars (optional): `OPENROUTER_MODEL` (default mistralai/mistral-7b-instruct), `USE_JSON_FORMAT`, `OPENROUTER_REFERRER`, `OPENROUTER_APP`
- Vercel will build the Python function from `api/index.py`; all routes rewrite to the FastAPI app.

## Features
- User dashboard: rate 1–5, submit review, receive AI response; data persisted.
- Admin dashboard: live-updating table (polls `/admin/data`), shows rating, review, AI summary, AI actions; analytics (count, avg rating).
- Shared datastore: SQLite via SQLAlchemy.
- LLM: OpenRouter-compatible chat API; graceful fallback if no key configured.

## Notes
- Adjust polling in `templates/admin.html` if needed.
- To change model/provider, edit `call_llm` in `app/main.py`.
