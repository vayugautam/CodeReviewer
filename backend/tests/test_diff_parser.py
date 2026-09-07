"""
tests/test_diff_parser.py — unit tests for the diff parser.
"""

from __future__ import annotations

from app.schemas.diff import LineType
from app.schemas.github import PRFile
from app.services.diff_parser import _parse_patch, parse_pr_files


# A minimal but realistic patch string
SAMPLE_PATCH = """\
@@ -1,4 +1,5 @@
 def greet(name):
-    print("hello " + name)
+    print("hello", name)
+    return f"hello {name}"
 
 def main():"""


class TestParsePatch:
    def test_returns_one_hunk(self):
        hunks = _parse_patch(SAMPLE_PATCH)
        assert len(hunks) == 1

    def test_hunk_header_parsed_correctly(self):
        hunks = _parse_patch(SAMPLE_PATCH)
        h = hunks[0]
        assert h.old_start == 1
        assert h.old_count == 4
        assert h.new_start == 1
        assert h.new_count == 5

    def test_line_types_correct(self):
        hunks = _parse_patch(SAMPLE_PATCH)
        types = [line.line_type for line in hunks[0].lines]
        assert LineType.CONTEXT in types
        assert LineType.ADDED in types
        assert LineType.REMOVED in types

    def test_added_lines_content(self):
        hunks = _parse_patch(SAMPLE_PATCH)
        added = [l for l in hunks[0].lines if l.line_type == LineType.ADDED]
        contents = [l.content for l in added]
        assert '    print("hello", name)' in contents
        assert '    return f"hello {name}"' in contents

    def test_removed_lines_content(self):
        hunks = _parse_patch(SAMPLE_PATCH)
        removed = [l for l in hunks[0].lines if l.line_type == LineType.REMOVED]
        assert removed[0].content == '    print("hello " + name)'

    def test_empty_patch_returns_empty(self):
        assert _parse_patch("") == []


MULTI_HUNK_PATCH = """\
@@ -1,3 +1,3 @@
 line1
-line2_old
+line2_new
 line3
@@ -10,3 +10,4 @@
 lineA
+lineB_new
 lineC
 lineD"""


class TestMultiHunkPatch:
    def test_two_hunks_parsed(self):
        hunks = _parse_patch(MULTI_HUNK_PATCH)
        assert len(hunks) == 2

    def test_second_hunk_start(self):
        hunks = _parse_patch(MULTI_HUNK_PATCH)
        assert hunks[1].new_start == 10


class TestParsePrFiles:
    def test_added_file_is_parsed(self):
        file = PRFile(filename="new.py", status="added", additions=1, deletions=0, changes=1, patch="@@ -0,0 +1 @@\n+value = 1")
        result = parse_pr_files([file])[0]
        assert result.status == "added" and result.added_lines[0].content == "value = 1"

    def test_deleted_file_keeps_removed_line_information(self):
        file = PRFile(filename="old.py", status="removed", additions=0, deletions=1, changes=1, patch="@@ -1 +0,0 @@\n-old = True")
        result = parse_pr_files([file])[0]
        assert result.status == "removed" and len(result.added_lines) == 0

    def test_binary_file_has_no_patch(self):
        pr_file = PRFile(
            filename="image.png",
            status="added",
            additions=0,
            deletions=0,
            changes=0,
            patch=None,
        )
        result = parse_pr_files([pr_file])
        assert result[0].has_patch is False
        assert result[0].is_binary is True

    def test_missing_patch_on_non_binary_file_is_marked_unavailable(self):
        file = PRFile(filename="large.py", status="modified", additions=50, deletions=1, changes=51, patch=None)
        result = parse_pr_files([file])[0]
        assert result.has_patch is False and result.is_binary is False

    def test_normal_file_parsed(self):
        pr_file = PRFile(
            filename="app.py",
            status="modified",
            additions=2,
            deletions=1,
            changes=3,
            patch=SAMPLE_PATCH,
        )
        result = parse_pr_files([pr_file])
        assert result[0].has_patch is True
        assert result[0].is_binary is False
        assert len(result[0].hunks) == 1

    def test_added_lines_property(self):
        pr_file = PRFile(
            filename="app.py",
            status="modified",
            additions=2,
            deletions=1,
            changes=3,
            patch=SAMPLE_PATCH,
        )
        result = parse_pr_files([pr_file])
        added = result[0].added_lines
        assert len(added) == 2
        assert all(l.line_type == LineType.ADDED for l in added)
