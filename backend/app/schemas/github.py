"""
schemas/github.py — Pydantic models for everything GitHub-related.

Why Pydantic?
  Pydantic converts raw dict data (from the GitHub API JSON response)
  into typed Python objects and validates them at parse-time.  If a
  field is missing or the wrong type, you get a clear error immediately
  rather than a silent None that crashes later.

Interview tip: "I use Pydantic as my data-contract layer.  Every piece
of external data — GitHub API, LLM response — is parsed through a
Pydantic model before the rest of the application touches it."
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ─── Request ─────────────────────────────────────────────────────────────────

class PRUrlRequest(BaseModel):
    """Body of POST /api/review/fetch-pr."""
    pr_url: str = Field(..., min_length=1, max_length=2048, description="Full GitHub pull-request URL")


# ─── GitHub raw data models ───────────────────────────────────────────────────

class PRFile(BaseModel):
    """
    One changed file as returned by GitHub's
    GET /repos/{owner}/{repo}/pulls/{number}/files endpoint.

    'patch' contains the unified diff for this file.
    It is Optional because binary files and very large files may have no patch.
    """
    filename: str
    status: str                      # added | modified | removed | renamed
    additions: int
    deletions: int
    changes: int
    patch: str | None = None         # unified diff string — may be absent


# ─── Parsed PR response ───────────────────────────────────────────────────────

class PRData(BaseModel):
    """
    The structured pull-request object we hand to the rest of the
    application after fetching and normalising the GitHub API response.
    """
    # Identifiers
    owner: str
    repo: str
    number: int

    # Human-readable metadata
    title: str
    description: str                 # PR body — may be empty string
    author: str
    state: str                       # open | closed | merged

    # Branch info
    head_branch: str                 # source (feature) branch
    base_branch: str                 # target (usually main/master)

    # Stats
    additions: int
    deletions: int
    changed_files: int

    # The actual content we analyse
    files: list[PRFile]
