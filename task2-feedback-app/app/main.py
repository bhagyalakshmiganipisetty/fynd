import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv
import httpx
from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()
# Paths and settings
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)
DB_PATH = DATA_DIR / "app.db"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct")
OPENROUTER_REFERRER = os.getenv("OPENROUTER_REFERRER", "https://localhost")
OPENROUTER_APP = os.getenv("OPENROUTER_APP", "fynd-feedback-app")
USE_JSON_FORMAT = os.getenv("USE_JSON_FORMAT", "true").lower() == "true"

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer, nullable=False)
    review = Column(String, nullable=False)
    ai_response = Column(String, nullable=True)
    ai_summary = Column(String, nullable=True)
    ai_actions = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task 2 - Feedback Dashboards")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class SubmissionOut(BaseModel):
    id: int
    rating: int
    review: str
    ai_response: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_actions: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True


async def call_llm(review: str, rating: int) -> dict:
    """
    Call OpenRouter (OpenAI-compatible) to generate user-facing response,
    summary, and recommended actions. Falls back to deterministic stubs if
    no API key is configured so the app remains usable offline.
    """
    system_prompt = (
        "You are a concise feedback assistant. Respond ONLY with JSON. "
        "Keys: user_response (string, <60 words, empathetic), "
        "summary (one sentence), actions (array of 3 concise bullet strings). "
        "Do not include markdown or extra text."
    )
    user_prompt = f"Rating: {rating}. Review: {review}"

    if not OPENROUTER_API_KEY:
        # Offline fallback to keep the app functional
        return {
            "user_response": f"Thanks for the {rating}-star review! We appreciate your feedback.",
            "summary": f"Customer rated {rating} stars and mentioned: {review[:80]}...",
            "actions": [
                "Share feedback with the team",
                "Improve response time",
                "Follow up with the customer",
            ],
        }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_REFERRER,
        "X-Title": OPENROUTER_APP,
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 180,
    }
    if USE_JSON_FORMAT:
        payload["response_format"] = {"type": "json_object"}

    def validate_llm_payload(content: str) -> dict:
        try:
            data = json.loads(content)
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        # Normalize actions to list
        actions = data.get("actions")
        if isinstance(actions, str):
            actions = [actions]
        if actions is None:
            actions = []
        return {
            "user_response": str(data.get("user_response", content))[:400],
            "summary": str(data.get("summary", ""))[:300],
            "actions": actions,
        }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            validated = validate_llm_payload(content)
            if validated:
                return validated
            # If model ignored JSON mode, wrap raw content
            return {
                "user_response": content,
                "summary": f"Customer rated {rating} stars; key note: {review[:60]}...",
                "actions": [
                    "Thank the user",
                    "Log the feedback",
                    "Plan a follow-up improvement",
                ],
            }
    except Exception as e:
        # Graceful fallback on errors
        return {
            "user_response": f"Thanks for sharing! (fallback due to error: {e})",
            "summary": f"Customer rated {rating} stars.",
            "actions": [
                "Review the feedback",
                "Acknowledge the user",
                "Plan improvements",
            ],
        }


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def user_dashboard(request: Request):
    return templates.TemplateResponse("user.html", {"request": request})


@app.post("/submit")
async def submit_feedback(
    request: Request,
    rating: int = Form(...),
    review: str = Form(...),
):
    db = next(get_db())
    llm_result = await call_llm(review, rating)

    submission = Submission(
        rating=rating,
        review=review,
        ai_response=llm_result.get("user_response"),
        ai_summary=llm_result.get("summary"),
        ai_actions="\n".join(llm_result.get("actions", [])),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # Return user-facing response
    return templates.TemplateResponse(
        "user.html",
        {
            "request": request,
            "message": llm_result.get("user_response"),
            "last_review": review,
            "last_rating": rating,
        },
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    db = next(get_db())
    subs: List[Submission] = db.query(Submission).order_by(Submission.created_at.desc()).all()
    total = len(subs)
    avg_rating = round(sum(s.rating for s in subs) / total, 2) if total else 0
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "subs": subs,
            "total": total,
            "avg_rating": avg_rating,
        },
    )


@app.get("/admin/data", response_class=HTMLResponse)
async def admin_data(request: Request):
    db = next(get_db())
    subs: List[Submission] = db.query(Submission).order_by(Submission.created_at.desc()).all()
    total = len(subs)
    avg_rating = round(sum(s.rating for s in subs) / total, 2) if total else 0
    return templates.TemplateResponse(
        "admin_table.html",
        {
            "request": request,
            "subs": subs,
            "total": total,
            "avg_rating": avg_rating,
        },
    )


@app.get("/api/submissions", response_model=List[SubmissionOut])
async def api_submissions():
    db = next(get_db())
    subs: List[Submission] = db.query(Submission).order_by(Submission.created_at.desc()).all()
    return subs
