"""HTTP boundary for PR metadata and the complete review workflow."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.github import PRData, PRUrlRequest
from app.schemas.review import AnalyzeResponse
from app.services.github_service import GitHubAPIError, InvalidPRURLError, PRNotFoundError, fetch_pull_request
from app.services.llm_service import LLMServiceError
from app.services.review_service import review_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/review", tags=["review"])


@router.post("/fetch-pr", response_model=PRData)
def fetch_pr(body: PRUrlRequest) -> PRData:
    """Fetch public PR metadata only; useful for checking GitHub connectivity."""
    try:
        return fetch_pull_request(body.pr_url)
    except InvalidPRURLError as exc:
        raise HTTPException(status_code=422, detail="Enter a valid GitHub pull-request URL.") from exc
    except PRNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Pull request not found or is not public.") from exc
    except GitHubAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_pr(body: PRUrlRequest) -> AnalyzeResponse:
    """Run the GitHub -> parse -> rules -> Gemini -> validate -> merge pipeline."""
    try:
        return review_service.analyze(body.pr_url)
    except InvalidPRURLError as exc:
        raise HTTPException(status_code=422, detail="Enter a valid https://github.com/owner/repo/pull/123 URL.") from exc
    except PRNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Pull request not found or is not public.") from exc
    except GitHubAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LLMServiceError as exc:
        logger.warning("LLM review failed: %s", exc)
        raise HTTPException(status_code=503, detail="The AI review service could not complete the review. Please try again.") from exc
