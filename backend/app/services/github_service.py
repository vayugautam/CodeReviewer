"""
services/github_service.py — responsible for all GitHub REST API interaction.

Design decisions worth mentioning in an interview:
  1. Single Responsibility: this file does ONLY GitHub I/O. No analysis logic.
  2. httpx (not requests): httpx has first-class async support, better
     timeout handling, and keeps the door open for async endpoints later.
     For now we use the synchronous client because FastAPI can run sync
     route handlers in a thread pool automatically.
  3. Read-only: we only call GET endpoints.  We never POST, PATCH, or DELETE.
  4. Token optional: a GitHub token is not required for public repos, but
     providing one raises the rate-limit from 60 to 5,000 requests/hour.

GitHub REST API endpoints used:
  GET /repos/{owner}/{repo}/pulls/{pull_number}
    → returns the PR metadata (title, author, branches, stats, …)

  GET /repos/{owner}/{repo}/pulls/{pull_number}/files
    → returns a list of changed files, each with its unified diff patch

Both return JSON. The base URL is https://api.github.com.

How a PR URL is parsed:
  https://github.com/owner/repo/pull/42
                     ─────  ────       ──
  We split on "/" and pick out positions -4 (owner), -3 (repo), -1 (number).
  We validate the format with a regex so we give the caller a clear error
  for bad URLs instead of a confusing IndexError.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

import httpx

from app.config import settings
from app.schemas.github import PRData, PRFile

# ── Constants ─────────────────────────────────────────────────────────────────

GITHUB_API_BASE = "https://api.github.com"

# Matches: https://github.com/{owner}/{repo}/pull/{number}
# Optional trailing slash and query-string allowed.
_PR_URL_PATTERN = re.compile(
    r"^/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/pull/(?P<number>[1-9]\d*)/?$"
)

# GitHub returns at most 300 files per PR; their API is paginated but
# for a portfolio project we accept this limit and document it clearly.
_MAX_FILES_PER_PAGE = 100


# ── Exceptions ────────────────────────────────────────────────────────────────

class GitHubServiceError(Exception):
    """Base class for errors coming out of this service."""


class InvalidPRURLError(GitHubServiceError):
    """The URL does not look like a valid GitHub PR URL."""


class PRNotFoundError(GitHubServiceError):
    """The PR or repository does not exist, or the repo is private."""


class GitHubAPIError(GitHubServiceError):
    """Unexpected HTTP error from the GitHub API."""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_pr_url(pr_url: str) -> tuple[str, str, int]:
    """
    Extract (owner, repo, pull_number) from a GitHub PR URL.

    Raises InvalidPRURLError for anything that does not match the pattern.
    """
    parsed = urlparse(pr_url.strip())
    # This allowlist is intentional: the user input is never fetched directly,
    # preventing an arbitrary URL from becoming an SSRF request.
    if parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.username or parsed.password:
        match = None
    else:
        match = _PR_URL_PATTERN.fullmatch(parsed.path)
    if not match:
        raise InvalidPRURLError(
            f"'{pr_url}' is not a valid GitHub pull-request URL. "
            "Expected format: https://github.com/owner/repo/pull/123"
        )
    return match.group("owner"), match.group("repo"), int(match.group("number"))


def _build_headers() -> dict[str, str]:
    """
    Build the HTTP headers for every GitHub API request.

    We always request the v3 JSON media type.
    If a token is configured we add it as a Bearer token to raise rate limits.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


def _handle_response_errors(response: httpx.Response, context: str) -> None:
    """
    Centralised error mapping for GitHub API HTTP responses.

    404 → PRNotFoundError  (repo private, or PR doesn't exist)
    403 → GitHubAPIError   (rate-limited or forbidden)
    anything else 4xx/5xx → GitHubAPIError
    """
    if response.status_code == 200:
        return
    if response.status_code == 404:
        raise PRNotFoundError(
            f"GitHub returned 404 for {context}. "
            "The repository may be private, or the PR number may be wrong."
        )
    if response.status_code == 403:
        raise GitHubAPIError(
            "GitHub returned 403 — you are likely rate-limited. "
            "Set GITHUB_TOKEN in your .env to increase the limit."
        )
    raise GitHubAPIError(
        "GitHub could not complete this request. Please try again later."
    )


# ── Public service function ───────────────────────────────────────────────────

def fetch_pull_request(pr_url: str) -> PRData:
    """
    Fetch all data needed to review a pull request.

    Steps:
      1. Parse the URL to get owner / repo / number.
      2. GET the PR metadata.
      3. GET the list of changed files (with patches).
      4. Assemble a PRData object and return it.

    This function is synchronous. FastAPI runs sync functions in a thread
    pool so the event loop is never blocked.
    """
    owner, repo, number = _parse_pr_url(pr_url)
    headers = _build_headers()

    # Use a single httpx client for connection pooling across both requests.
    try:
        client_context = httpx.Client(timeout=settings.github_timeout_seconds)
        client = client_context.__enter__()
        try:
        # ── 1. Fetch PR metadata ──────────────────────────────────────────
            pr_url_api = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{number}"
            pr_response = client.get(pr_url_api, headers=headers)
            _handle_response_errors(pr_response, context=f"PR #{number} in {owner}/{repo}")
            pr_json = pr_response.json()

        # ── 2. Fetch changed files ────────────────────────────────────────
            files_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{number}/files"
            files_response = client.get(files_url, headers=headers, params={"per_page": _MAX_FILES_PER_PAGE})
            _handle_response_errors(files_response, context=f"files for PR #{number}")
            files_json = files_response.json()
        finally:
            client_context.__exit__(None, None, None)
    except httpx.TimeoutException as exc:
        raise GitHubAPIError("GitHub did not respond in time. Please try again.") from exc
    except httpx.HTTPError as exc:
        raise GitHubAPIError("Unable to reach GitHub. Please try again.") from exc
    except ValueError as exc:
        raise GitHubAPIError("GitHub returned an unexpected response.") from exc

    # ── 3. Parse files list ───────────────────────────────────────────────
    files: list[PRFile] = []
    for f in files_json:
        files.append(
            PRFile(
                filename=f["filename"],
                status=f["status"],
                additions=f.get("additions", 0),
                deletions=f.get("deletions", 0),
                changes=f.get("changes", 0),
                # 'patch' is absent for binary files and very large files
                patch=f.get("patch"),
            )
        )

    # ── 4. Assemble and return ────────────────────────────────────────────
    return PRData(
        owner=owner,
        repo=repo,
        number=number,
        title=pr_json["title"],
        description=pr_json.get("body") or "",
        author=pr_json["user"]["login"],
        state=pr_json["state"],
        head_branch=pr_json["head"]["ref"],
        base_branch=pr_json["base"]["ref"],
        additions=pr_json.get("additions", 0),
        deletions=pr_json.get("deletions", 0),
        changed_files=pr_json.get("changed_files", 0),
        files=files,
    )
