# Fynd AI Intern – Take Home Assessment Report

## Task 1: Rating Prediction via Prompting
- **Dataset**: Yelp Reviews (Kaggle: omkarsabnis/yelp-reviews-dataset); sampled 200 rows.
- **LLM**: OpenRouter (`mistralai/mistral-7b-instruct`), JSON mode on, temp=0.
- **Prompt strategies**:
  1) Baseline: JSON-only rating + brief reason.  
  2) CoT-lite: brief aspect reasoning then JSON.  
  3) Self-check: draft → validate/fix range/JSON → final JSON.  
  4) Rubric-guided: explicit 1–5 rubric, JSON-only.  
- **Validation**: strict JSON parsing; rating range 1–5 enforced; repair pass; JSON validity tracked.
- **Evaluation (200-row run)**:
  - Rubric: acc 0.70, JSON valid 1.0  
  - CoT: acc 0.685, JSON valid 1.0  
  - Self-check: acc 0.67, JSON valid 1.0  
  - Baseline: acc 0.635, JSON valid 1.0  
  - ML baseline (char TF-IDF + LR): ~0.38 acc (40-row test)  
- **Takeaways**: Rubric performs best; CoT close; self-check helps but trails; baseline lags. JSON validity stable at 1.0 with current parsing/repair.

## Task 2: Two-Dashboard AI Feedback System
- **Stack**: FastAPI + Jinja; SQLite/managed Postgres via `DATABASE_URL`; OpenRouter LLM for user response, admin summary, and actions.
- **Endpoints**:
  - `POST /submit`: store rating/review; call LLM; persist user_response/summary/actions.
  - `GET /admin`: admin dashboard; polls `/admin/data` for live updates.
  - `GET /api/submissions`: JSON feed.
- **Dashboards**:
  - User (public): rating + review form; shows AI response.
  - Admin (internal): live table with rating, review, AI summary, AI actions; totals and avg rating; auto-refresh.
- **LLM**: default `mistralai/mistral-7b-instruct`; JSON prompts; fallbacks if API fails.
- **Deployment**: Dockerfile + `vercel.json` for Vercel Docker deploy. Envs: `OPENROUTER_API_KEY`, `DATABASE_URL` (managed DB), optional `OPENROUTER_MODEL`, `USE_JSON_FORMAT`, `OPENROUTER_REFERRER`, `OPENROUTER_APP`.

## Final Submission Checklist
- GitHub repo: [add link]
- Report: `report.md` (this file) or PDF export
- User dashboard URL: [add after deploy]
- Admin dashboard URL: [add after deploy]
