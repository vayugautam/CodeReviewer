"""
main.py — FastAPI application entry-point.

This file does three things:
  1. Creates the FastAPI app instance.
  2. Configures CORS so the React frontend (running on a different port)
     can call the API.
  3. Mounts all routers.

Why CORS matters:
  Browsers enforce the Same-Origin Policy — a page at localhost:5173 cannot
  make XHR/fetch calls to localhost:8000 unless the server explicitly allows
  it via CORS headers.  FastAPI's CORSMiddleware adds those headers.

  In production you would set allow_origins to your real domain only.
  During development we allow the Vite dev-server origin from settings.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.review import router as review_router
from app.config import settings

# Configure basic logging so we can see service-level log messages
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="AI CodeReview API",
    description="LLM-powered GitHub Pull Request Analyzer",
    version="0.1.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
  allow_origins=[
    settings.frontend_origin,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
  ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(review_router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Simple liveness probe — confirms the server is running."""
    return {"status": "ok"}
