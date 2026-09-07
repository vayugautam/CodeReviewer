"""
schemas/diff.py — internal models for representing a parsed Git diff.

These are NOT Pydantic models that come from external input; they are
plain dataclasses used internally after we parse the raw patch string.

Why dataclasses instead of Pydantic here?
  These objects are created by our own code (the diff parser), not
  from untrusted external input, so we don't need Pydantic's validation.
  Plain dataclasses are lighter and clearer for internal data structures.

Interview explanation of Git diff/patch:
  A "patch" (or "unified diff") is the standard way to represent changes
  between two versions of a file.  It looks like this:

    @@ -10,6 +10,7 @@        ← hunk header
     def foo():              ← context line (unchanged)
    -    old_line()          ← removed line (prefixed -)
    +    new_line()          ← added line   (prefixed +)
     return result           ← context line

  The hunk header "@@ -10,6 +10,7 @@" means:
    - In the OLD file: 6 lines starting at line 10
    - In the NEW file: 7 lines starting at line 10

  We only need to parse this well enough to (a) know which lines were
  added, and (b) give the LLM clean, labelled context.
  A production tool like 'libgit2' would parse this fully, but for our
  use case simple string processing is sufficient and far easier to
  explain in an interview.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class LineType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    CONTEXT = "context"


@dataclass
class DiffLine:
    """A single line inside a hunk."""
    line_type: LineType
    content: str          # the actual code content (without the leading +/-/ )
    new_lineno: int | None = None   # line number in the new file (added/context)
    old_lineno: int | None = None   # line number in the old file (removed/context)


@dataclass
class DiffHunk:
    """
    One contiguous block of changes inside a file diff.
    A single file can have multiple hunks (e.g. changes in different functions).
    """
    old_start: int        # starting line in old file
    old_count: int        # number of lines from old file
    new_start: int        # starting line in new file
    new_count: int        # number of lines in new file
    lines: list[DiffLine] = field(default_factory=list)


@dataclass
class ChangedFile:
    """
    Fully parsed representation of one changed file in the PR.
    This is what the rule analyzer and LLM service receive.
    """
    filename: str
    status: str                         # added | modified | removed | renamed
    additions: int
    deletions: int
    hunks: list[DiffHunk] = field(default_factory=list)
    is_binary: bool = False
    has_patch: bool = True              # False when GitHub returns no patch data

    @property
    def added_lines(self) -> list[DiffLine]:
        """Convenience: all lines that were added across every hunk."""
        return [
            line
            for hunk in self.hunks
            for line in hunk.lines
            if line.line_type == LineType.ADDED
        ]

    @property
    def all_lines(self) -> list[DiffLine]:
        """All lines (added + context) — useful for LLM context."""
        return [line for hunk in self.hunks for line in hunk.lines]
