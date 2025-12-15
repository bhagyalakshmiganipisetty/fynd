import os
import sys
from pathlib import Path

# Ensure project root on path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.main import app  # noqa: E402

# Define a basic health check route to reduce cold start confusion
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# Vercel's Python builder looks for `app` in this module.
