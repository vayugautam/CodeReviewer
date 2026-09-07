"""
tests/test_github_service.py — unit tests for GitHub URL parsing.
(We test the pure function; actual HTTP calls require integration tests.)
"""

import pytest
from app.services.github_service import _parse_pr_url, InvalidPRURLError


class TestParsePrUrl:
    def test_standard_url(self):
        owner, repo, number = _parse_pr_url("https://github.com/facebook/react/pull/27380")
        assert owner == "facebook"
        assert repo == "react"
        assert number == 27380

    def test_url_with_trailing_slash(self):
        owner, repo, number = _parse_pr_url("https://github.com/owner/repo/pull/1/")
        assert owner == "owner"
        assert repo == "repo"
        assert number == 1

    def test_url_with_query_params(self):
        owner, repo, number = _parse_pr_url(
            "https://github.com/vercel/next.js/pull/50000?diff=unified"
        )
        assert owner == "vercel"
        assert repo == "next.js"
        assert number == 50000

    def test_invalid_url_raises(self):
        with pytest.raises(InvalidPRURLError):
            _parse_pr_url("https://gitlab.com/owner/repo/merge_requests/1")

    def test_missing_pull_number_raises(self):
        with pytest.raises(InvalidPRURLError):
            _parse_pr_url("https://github.com/owner/repo")

    def test_not_a_url_raises(self):
        with pytest.raises(InvalidPRURLError):
            _parse_pr_url("owner/repo/pull/1")

    def test_pr_number_is_int(self):
        _, _, number = _parse_pr_url("https://github.com/django/django/pull/999")
        assert isinstance(number, int)
