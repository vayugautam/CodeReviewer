"""GitHub service contract tests with a fake httpx client."""

import pytest

from app.services import github_service
from app.services.github_service import GitHubAPIError, PRNotFoundError, fetch_pull_request


class Response:
    def __init__(self, status_code, payload):
        self.status_code, self._payload, self.text = status_code, payload, "upstream response"
    def json(self): return self._payload


class Client:
    def __init__(self, responses): self.responses = iter(responses)
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def get(self, *_, **__): return next(self.responses)


def install_client(monkeypatch, responses):
    monkeypatch.setattr(github_service.httpx, "Client", lambda **_: Client(responses))


def metadata():
    return {"title": "Title", "body": "", "user": {"login": "dev"}, "state": "open",
            "head": {"ref": "feature"}, "base": {"ref": "main"}, "additions": 1,
            "deletions": 0, "changed_files": 1}


def test_valid_pr_url_fetches_metadata_and_files(monkeypatch):
    install_client(monkeypatch, [Response(200, metadata()), Response(200, [{"filename": "a.py", "status": "modified", "additions": 1, "deletions": 0, "changes": 1, "patch": "@@ -1 +1 @@\n+x"}])])
    result = fetch_pull_request("https://github.com/acme/demo/pull/7")
    assert result.number == 7 and result.files[0].filename == "a.py"


def test_nonexistent_pr_is_mapped_to_not_found(monkeypatch):
    install_client(monkeypatch, [Response(404, {})])
    with pytest.raises(PRNotFoundError): fetch_pull_request("https://github.com/acme/demo/pull/7")


def test_upstream_api_failure_is_controlled(monkeypatch):
    install_client(monkeypatch, [Response(500, {})])
    with pytest.raises(GitHubAPIError): fetch_pull_request("https://github.com/acme/demo/pull/7")
