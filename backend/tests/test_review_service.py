"""Review orchestration tests use fakes; no network or Gemini key is needed."""

import pytest

from app.schemas.github import PRData, PRFile
from app.schemas.review import OverallStatus, ReviewResponse
from app.services.github_service import GitHubAPIError
from app.services.llm_service import LLMServiceError
from app.services.review_service import ReviewService, _bounded_files


def pr_data():
    return PRData(
        owner="acme", repo="demo", number=1, title="Fix handler", description="",
        author="dev", state="open", head_branch="fix", base_branch="main",
        additions=1, deletions=0, changed_files=1,
        files=[PRFile(filename="app.py", status="modified", additions=1, deletions=0, changes=1,
                      patch="@@ -1 +1 @@\n+print('debug')")],
    )


def test_successful_pipeline(monkeypatch):
    monkeypatch.setattr("app.services.review_service.fetch_pull_request", lambda _: pr_data())
    monkeypatch.setattr(
        "app.services.review_service.review_with_llm",
        lambda **_: ReviewResponse(summary="Looks safe.", overall_status=OverallStatus.APPROVE, findings=[]),
    )
    result = ReviewService().analyze("https://github.com/acme/demo/pull/1")
    assert result.review.summary == "Looks safe."
    assert any(f.source == "static" for f in result.review.findings)


def test_github_failure_stops_pipeline(monkeypatch):
    monkeypatch.setattr("app.services.review_service.fetch_pull_request", lambda _: (_ for _ in ()).throw(GitHubAPIError("down")))
    with pytest.raises(GitHubAPIError):
        ReviewService().analyze("https://github.com/acme/demo/pull/1")


def test_llm_failure_is_propagated(monkeypatch):
    monkeypatch.setattr("app.services.review_service.fetch_pull_request", lambda _: pr_data())
    monkeypatch.setattr("app.services.review_service.review_with_llm", lambda **_: (_ for _ in ()).throw(LLMServiceError("bad output")))
    with pytest.raises(LLMServiceError):
        ReviewService().analyze("https://github.com/acme/demo/pull/1")


def test_file_and_diff_limits_emit_clear_warnings(monkeypatch):
    from app.services import review_service
    monkeypatch.setattr(review_service.settings, "max_review_files", 1)
    monkeypatch.setattr(review_service.settings, "max_total_diff_chars", 5)
    files = [
        PRFile(filename="first.py", status="modified", additions=1, deletions=0, changes=1, patch="@@ -1 +1 @@\n+value"),
        PRFile(filename="second.py", status="modified", additions=1, deletions=0, changes=1, patch="@@ -1 +1 @@\n+other"),
    ]
    bounded, warnings = _bounded_files(files)
    assert len(bounded) == 1
    assert bounded[0].patch == "@@ -1"
    assert any("first 1 of 2" in warning for warning in warnings)
    assert any("truncated" in warning for warning in warnings)
