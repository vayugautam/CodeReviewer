"""
schemas/review.py — models for the final code review output.

This schema is the contract between the backend and the frontend.
It is also what the LLM must produce (as JSON), and what Pydantic
validates before we return the response.

Design principle: keep it flat and simple.  Every field should be
something a junior dev can read and immediately understand.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr


# ─── Enumerations ─────────────────────────────────────────────────────────────

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Category(str, Enum):
    SECURITY = "security"
    BUG = "bug"
    QUALITY = "quality"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"


class OverallStatus(str, Enum):
    APPROVE = "approve"
    NEEDS_CHANGES = "needs_changes"
    REVIEW = "review"


# ─── Finding ──────────────────────────────────────────────────────────────────

class Finding(BaseModel):
    """
    A single code issue found by either the rule-based analyzer
    or the LLM reviewer.

    'source' tells the UI (and the developer) whether this came from
    a deterministic rule or the LLM — useful for explaining confidence.
    """
    model_config = ConfigDict(extra="forbid")
    severity: Severity
    category: Category
    file: StrictStr
    line: StrictInt | None = Field(None, description="Line number in new file, if known")
    message: StrictStr = Field(..., description="What the problem is")
    suggestion: StrictStr = Field(..., description="How to fix it")
    rule: StrictStr | None = Field(None, description="Rule ID, set for static findings")
    source: StrictStr = Field("llm", description="'static' or 'llm'")


# ─── Full review ──────────────────────────────────────────────────────────────

class ReviewResponse(BaseModel):
    """
    The complete review object returned by POST /api/review/analyze.
    The LLM is asked to produce a JSON object matching this schema.
    """
    model_config = ConfigDict(extra="forbid")
    summary: StrictStr
    overall_status: OverallStatus
    findings: list[Finding] = Field(default_factory=list)


# ─── API response wrapper ─────────────────────────────────────────────────────

class AnalyzeResponse(BaseModel):
    """
    The full payload returned by the /analyze endpoint.
    Wraps the review with the PR metadata for the frontend.
    """
    pr_title: str
    pr_author: str
    pr_url: str
    head_branch: str
    base_branch: str
    additions: int
    deletions: int
    changed_files: int
    diff_preview: str | None = Field(None, description="Truncated read-only diff preview")
    analysis_warnings: list[str] = Field(default_factory=list)
    review: ReviewResponse
