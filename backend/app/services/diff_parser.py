"""
services/diff_parser.py — converts raw GitHub patch strings into structured objects.

Why we DON'T need a complete Git parser
────────────────────────────────────────
A real diff parser (like the one in libgit2 or GitPython) handles:
  - multiple codepage encodings, binary hunks, merge conflicts,
    submodule references, mode changes, extended headers, etc.

We only need to answer two questions:
  1. Which lines were added in this PR?      (for rule-based checks)
  2. What does the context look like?        (for the LLM prompt)

For that, simple line-by-line string parsing is more than enough and
is completely transparent — you can trace every step in a debugger.

Unified diff format recap (interview ready)
────────────────────────────────────────────
A unified diff is structured as one or more "hunks".
Each hunk starts with a header like:

  @@ -10,6 +10,7 @@ def my_function():
      │   │   │   └─ optional function context (ignored by us)
      │   │   └──── in the NEW file: 7 lines starting at line 10
      │   └──────── in the OLD file: 6 lines starting at line 10
      └──────────── hunk marker

Lines that follow the header are prefixed:
  ' ' (space) → context line  (unchanged, shown for readability)
  '+' (plus)  → added line
  '-' (minus) → removed line

We walk through each line, track the current line number, and emit
DiffLine / DiffHunk / ChangedFile objects.
"""

from __future__ import annotations

import re

from app.schemas.diff import ChangedFile, DiffHunk, DiffLine, LineType
from app.schemas.github import PRFile

# Matches the hunk header: @@ -old_start,old_count +new_start,new_count @@
# The count part (,N) is optional — Git omits it when N==1.
_HUNK_HEADER = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? \+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)


def _parse_patch(patch: str) -> list[DiffHunk]:
    """
    Parse a raw unified-diff patch string into a list of DiffHunk objects.

    This is the core parsing function.  It iterates through the patch
    line-by-line and builds up the hunk list incrementally.
    """
    hunks: list[DiffHunk] = []
    current_hunk: DiffHunk | None = None

    # These track the "cursor" position as we walk through lines
    old_lineno = 0
    new_lineno = 0

    for raw_line in patch.splitlines():
        # ── Hunk header? ─────────────────────────────────────────────────
        header_match = _HUNK_HEADER.match(raw_line)
        if header_match:
            # Save the previous hunk if there is one
            if current_hunk is not None:
                hunks.append(current_hunk)

            old_start = int(header_match.group("old_start"))
            old_count = int(header_match.group("old_count") or "1")
            new_start = int(header_match.group("new_start"))
            new_count = int(header_match.group("new_count") or "1")

            current_hunk = DiffHunk(
                old_start=old_start,
                old_count=old_count,
                new_start=new_start,
                new_count=new_count,
            )

            # Reset line-number cursors to the hunk's starting positions
            old_lineno = old_start
            new_lineno = new_start
            continue

        # If we haven't seen a hunk header yet, skip (shouldn't happen with
        # valid GitHub patches, but defensive is better).
        if current_hunk is None:
            continue

        # ── Classify the line ─────────────────────────────────────────────
        if raw_line.startswith("+"):
            line = DiffLine(
                line_type=LineType.ADDED,
                content=raw_line[1:],   # strip the leading '+'
                new_lineno=new_lineno,
            )
            new_lineno += 1

        elif raw_line.startswith("-"):
            line = DiffLine(
                line_type=LineType.REMOVED,
                content=raw_line[1:],   # strip the leading '-'
                old_lineno=old_lineno,
            )
            old_lineno += 1

        elif raw_line.startswith(" ") or raw_line == "":
            # Context lines start with a space; an empty string can appear
            # at the end of a patch — treat it as context.
            line = DiffLine(
                line_type=LineType.CONTEXT,
                content=raw_line[1:] if raw_line.startswith(" ") else "",
                old_lineno=old_lineno,
                new_lineno=new_lineno,
            )
            old_lineno += 1
            new_lineno += 1

        else:
            # Lines starting with '\', 'diff --git', etc. — skip them
            continue

        current_hunk.lines.append(line)

    # Don't forget the last hunk
    if current_hunk is not None:
        hunks.append(current_hunk)

    return hunks


def parse_pr_files(pr_files: list[PRFile]) -> list[ChangedFile]:
    """
    Convert a list of raw PRFile objects (straight from the GitHub API)
    into ChangedFile objects with fully parsed hunks.

    This is the public entry-point called by the review orchestrator.
    """
    changed_files: list[ChangedFile] = []

    for pr_file in pr_files:
        # ── Binary files ──────────────────────────────────────────────────
        # GitHub does not include a 'patch' key for binary files.
        # We mark them so the analyzer can skip them gracefully.
        if pr_file.patch is None:
            changed_files.append(
                ChangedFile(
                    filename=pr_file.filename,
                    status=pr_file.status,
                    additions=pr_file.additions,
                    deletions=pr_file.deletions,
                    hunks=[],
                    is_binary=(pr_file.additions == 0 and pr_file.deletions == 0),
                    has_patch=False,
                )
            )
            continue

        # ── Parse the patch ───────────────────────────────────────────────
        hunks = _parse_patch(pr_file.patch)
        changed_files.append(
            ChangedFile(
                filename=pr_file.filename,
                status=pr_file.status,
                additions=pr_file.additions,
                deletions=pr_file.deletions,
                hunks=hunks,
                is_binary=False,
                has_patch=True,
            )
        )

    return changed_files
