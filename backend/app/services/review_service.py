"""Readable orchestration for the complete, synchronous PR-review workflow."""

from __future__ import annotations

import logging

from app.schemas.review import AnalyzeResponse, Finding, ReviewResponse
from app.schemas.github import PRFile
from app.config import settings
from app.services.diff_parser import parse_pr_files
from app.services.github_service import fetch_pull_request
from app.services.llm_service import review_with_llm
from app.services.rule_analyzer import rule_analyzer

logger = logging.getLogger(__name__)


class ReviewServiceError(Exception):
    """A controlled failure from one stage of the review pipeline."""


def _diff_preview(changed_files: list[object], limit: int = 20_000) -> str:
    """Return a display-only preview; it is never executed or rendered as HTML."""
    chunks: list[str] = []
    for changed_file in changed_files:
        filename = getattr(changed_file, "filename")
        chunks.append(f"--- {filename} ---")
        for hunk in getattr(changed_file, "hunks"):
            chunks.append(f"@@ -{hunk.old_start},{hunk.old_count} +{hunk.new_start},{hunk.new_count} @@")
            for line in hunk.lines:
                prefix = {"added": "+", "removed": "-", "context": " "}[line.line_type.value]
                chunks.append(f"{prefix}{line.content}")
    preview = "\n".join(chunks)
    return preview[:limit] + ("\n[Preview truncated]" if len(preview) > limit else "")


def _deduplicate(findings: list[Finding]) -> list[Finding]:
    """Keep the deterministic report when an LLM finding names the same issue."""
    result: list[Finding] = []
    seen: set[tuple[str, int | None, str]] = set()
    for finding in findings:
        key = (finding.file.lower(), finding.line, finding.message.strip().lower())
        if key not in seen:
            seen.add(key)
            result.append(finding)
    return result


def _bounded_files(files: list[PRFile]) -> tuple[list[PRFile], list[str]]:
    """Bound work before parsing; preserve input order and report every omission."""
    warnings: list[str] = []
    selected = files[: settings.max_review_files]
    if len(files) > len(selected):
        warnings.append(f"Only the first {len(selected)} of {len(files)} changed files were analyzed.")

    total = 0
    bounded: list[PRFile] = []
    skipped_without_patch = 0
    for file in selected:
        if file.patch is None:
            skipped_without_patch += 1
            bounded.append(file)
            continue
        remaining = settings.max_total_diff_chars - total
        if remaining <= 0:
            continue
        patch = file.patch[:remaining]
        if len(patch) < len(file.patch):
            warnings.append(f"Diff content was truncated at {settings.max_total_diff_chars:,} characters.")
        total += len(patch)
        bounded.append(file.model_copy(update={"patch": patch}))
    if len(bounded) < len(selected):
        warnings.append("Some files were skipped because the total diff-size limit was reached.")
    if skipped_without_patch:
        warnings.append(f"Skipped detailed analysis for {skipped_without_patch} binary or unsupported file(s) without a patch.")
    if total > settings.max_llm_diff_chars:
        warnings.append(f"Gemini receives at most {settings.max_llm_diff_chars:,} diff characters; changed lines are prioritized.")
    return bounded, warnings


class ReviewService:
    """Coordinates GitHub retrieval, parsing, rules, Gemini, and result shaping."""

    def analyze(self, pr_url: str) -> AnalyzeResponse:
        # 1-2. The GitHub service validates the allowlisted URL before making API calls.
        pr_data = fetch_pull_request(pr_url)
        # 3-4. Convert GitHub patches to internal structured diff objects.
        bounded_files, warnings = _bounded_files(pr_data.files)
        changed_files = parse_pr_files(bounded_files)
        # 5. Deterministic checks are cheap and run before the LLM.
        static_findings = rule_analyzer.analyze(changed_files)
        # 6-9. Gemini receives metadata, diff, and static results, and validates with one repair attempt.
        llm_review = review_with_llm(
            pr_title=pr_data.title,
            pr_description=pr_data.description,
            changed_files=changed_files,
            static_findings=static_findings,
        )
        # 10-11. Merge and remove exact same-location/message duplicates.
        findings = _deduplicate(static_findings + llm_review.findings)
        logger.info("Review completed for PR #%s with %d findings", pr_data.number, len(findings))
        return AnalyzeResponse(
            pr_title=pr_data.title,
            pr_author=pr_data.author,
            pr_url=pr_url,
            head_branch=pr_data.head_branch,
            base_branch=pr_data.base_branch,
            additions=pr_data.additions,
            deletions=pr_data.deletions,
            changed_files=pr_data.changed_files,
            diff_preview=_diff_preview(changed_files),
            analysis_warnings=warnings,
            review=ReviewResponse(
                summary=llm_review.summary,
                overall_status=llm_review.overall_status,
                findings=findings,
            ),
        )


review_service = ReviewService()
