"""
tests/test_rule_analyzer.py — unit tests for every rule in RuleBasedAnalyzer.

Testing philosophy:
  Each test is isolated and tests ONE rule.
  We build the minimal ChangedFile/DiffHunk/DiffLine structure needed —
  no mocking framework required because our code has no external dependencies.

  We test:
    1. Positive case:  the rule fires when it should.
    2. Negative case:  the rule does NOT fire on clean code.
    3. Edge cases:     removed lines are NOT flagged (only added lines matter).
"""

from __future__ import annotations

import pytest

from app.schemas.diff import ChangedFile, DiffHunk, DiffLine, LineType
from app.schemas.review import Category, Severity
from app.services.rule_analyzer import RuleBasedAnalyzer, rule_analyzer


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_file(filename: str, added_lines: list[str], removed_lines: list[str] | None = None) -> ChangedFile:
    """
    Convenience factory: build a ChangedFile with one hunk containing
    the given added and (optionally) removed lines.
    """
    lines: list[DiffLine] = []
    for i, content in enumerate(added_lines, start=1):
        lines.append(DiffLine(line_type=LineType.ADDED, content=content, new_lineno=i))
    for i, content in enumerate(removed_lines or [], start=1):
        lines.append(DiffLine(line_type=LineType.REMOVED, content=content, old_lineno=i))

    hunk = DiffHunk(old_start=1, old_count=len(removed_lines or []), new_start=1, new_count=len(added_lines), lines=lines)
    return ChangedFile(filename=filename, status="modified", additions=len(added_lines), deletions=len(removed_lines or []), hunks=[hunk])


def get_rule_ids(findings) -> list[str]:
    return [f.rule for f in findings]


# ─── Rule: debug/console-log ──────────────────────────────────────────────────

class TestConsoleLog:
    def test_fires_on_console_log(self):
        f = make_file("app.js", ['  console.log("hello world");'])
        findings = rule_analyzer.analyze([f])
        assert "debug/console-log" in get_rule_ids(findings)

    def test_fires_on_console_log_no_space(self):
        f = make_file("util.js", ["console.log('debug')"])
        findings = rule_analyzer.analyze([f])
        assert "debug/console-log" in get_rule_ids(findings)

    def test_no_fire_on_clean_js(self):
        f = make_file("app.js", ["const x = 42;", 'logger.info("hello");'])
        findings = rule_analyzer.analyze([f])
        assert "debug/console-log" not in get_rule_ids(findings)

    def test_does_not_fire_on_removed_console_log(self):
        """Removing a console.log is GOOD — we should not flag it."""
        f = make_file("app.js", added_lines=[], removed_lines=['console.log("old debug")'])
        findings = rule_analyzer.analyze([f])
        assert "debug/console-log" not in get_rule_ids(findings)

    def test_severity_is_low(self):
        f = make_file("app.js", ["console.log('x')"])
        findings = rule_analyzer.analyze([f])
        console_findings = [x for x in findings if x.rule == "debug/console-log"]
        assert console_findings[0].severity == Severity.LOW

    def test_category_is_quality(self):
        f = make_file("app.js", ["console.log('x')"])
        findings = rule_analyzer.analyze([f])
        console_findings = [x for x in findings if x.rule == "debug/console-log"]
        assert console_findings[0].category == Category.QUALITY


# ─── Rule: debug/print-statement ──────────────────────────────────────────────

class TestPrintStatement:
    def test_fires_on_print(self):
        f = make_file("main.py", ['print("hello")'])
        findings = rule_analyzer.analyze([f])
        assert "debug/print-statement" in get_rule_ids(findings)

    def test_fires_on_print_with_space_before_paren(self):
        f = make_file("main.py", ["print ('debug value')"])
        findings = rule_analyzer.analyze([f])
        assert "debug/print-statement" in get_rule_ids(findings)

    def test_no_fire_on_clean_python(self):
        f = make_file("main.py", ["logger.info('hello')", "x = compute()"])
        findings = rule_analyzer.analyze([f])
        assert "debug/print-statement" not in get_rule_ids(findings)

    def test_does_not_fire_on_removed_print(self):
        f = make_file("main.py", added_lines=[], removed_lines=['print("old debug")'])
        findings = rule_analyzer.analyze([f])
        assert "debug/print-statement" not in get_rule_ids(findings)

    def test_fires_with_variable_arg(self):
        f = make_file("utils.py", ["print(response.status_code)"])
        findings = rule_analyzer.analyze([f])
        assert "debug/print-statement" in get_rule_ids(findings)


# ─── Rule: debug/system-out-println ───────────────────────────────────────────

class TestSystemOutPrintln:
    def test_fires_on_system_out_println(self):
        f = make_file("Main.java", ['System.out.println("debug");'])
        findings = rule_analyzer.analyze([f])
        assert "debug/system-out-println" in get_rule_ids(findings)

    def test_no_fire_on_clean_java(self):
        f = make_file("Main.java", ["logger.info(message);"])
        findings = rule_analyzer.analyze([f])
        assert "debug/system-out-println" not in get_rule_ids(findings)

    def test_does_not_fire_on_removed_line(self):
        f = make_file("Main.java", added_lines=[], removed_lines=["System.out.println(x);"])
        findings = rule_analyzer.analyze([f])
        assert "debug/system-out-println" not in get_rule_ids(findings)


# ─── Rule: quality/todo ───────────────────────────────────────────────────────

class TestTodoFixme:
    def test_fires_on_todo(self):
        f = make_file("service.py", ["# TODO: refactor this"])
        findings = rule_analyzer.analyze([f])
        assert "quality/todo" in get_rule_ids(findings)

    def test_fires_on_fixme(self):
        f = make_file("service.py", ["// FIXME: broken edge case"])
        findings = rule_analyzer.analyze([f])
        assert "quality/todo" in get_rule_ids(findings)

    def test_fires_on_hack(self):
        f = make_file("service.py", ["# HACK: workaround for bug #123"])
        findings = rule_analyzer.analyze([f])
        assert "quality/todo" in get_rule_ids(findings)

    def test_fires_case_insensitive(self):
        f = make_file("service.py", ["# todo: lowercase works too"])
        findings = rule_analyzer.analyze([f])
        assert "quality/todo" in get_rule_ids(findings)

    def test_no_fire_on_normal_comment(self):
        f = make_file("service.py", ["# This function handles authentication"])
        findings = rule_analyzer.analyze([f])
        assert "quality/todo" not in get_rule_ids(findings)

    def test_severity_is_low(self):
        f = make_file("service.py", ["# TODO: implement"])
        findings = rule_analyzer.analyze([f])
        todo_findings = [x for x in findings if x.rule == "quality/todo"]
        assert todo_findings[0].severity == Severity.LOW


# ─── Rule: security/hardcoded-secret ──────────────────────────────────────────

class TestHardcodedSecret:
    def test_fires_on_hardcoded_password(self):
        f = make_file("config.py", ['password = "supersecret123"'])
        findings = rule_analyzer.analyze([f])
        assert "security/hardcoded-secret" in get_rule_ids(findings)

    def test_fires_on_api_key(self):
        f = make_file("client.py", ['api_key = "sk-abcdefghijklmnop"'])
        findings = rule_analyzer.analyze([f])
        assert "security/hardcoded-secret" in get_rule_ids(findings)

    def test_fires_on_secret(self):
        f = make_file("settings.py", ["SECRET = 'mysecretvalue'"])
        findings = rule_analyzer.analyze([f])
        assert "security/hardcoded-secret" in get_rule_ids(findings)

    def test_fires_on_token(self):
        f = make_file("auth.py", ['token = "Bearer eyJhbGciOiJIUz"'])
        findings = rule_analyzer.analyze([f])
        assert "security/hardcoded-secret" in get_rule_ids(findings)

    def test_no_fire_on_env_var_lookup(self):
        """Reading from env is safe — should not trigger."""
        f = make_file("config.py", ['password = os.getenv("PASSWORD")'])
        findings = rule_analyzer.analyze([f])
        assert "security/hardcoded-secret" not in get_rule_ids(findings)

    def test_no_fire_on_empty_string_assignment(self):
        """password = "" — too short to be a real secret (< 4 chars)."""
        f = make_file("config.py", ['password = ""'])
        findings = rule_analyzer.analyze([f])
        assert "security/hardcoded-secret" not in get_rule_ids(findings)

    def test_severity_is_critical(self):
        f = make_file("config.py", ['api_key = "verylongsecretkey"'])
        findings = rule_analyzer.analyze([f])
        sec_findings = [x for x in findings if x.rule == "security/hardcoded-secret"]
        assert sec_findings[0].severity == Severity.CRITICAL

    def test_category_is_security(self):
        f = make_file("config.py", ['api_key = "verylongsecretkey"'])
        findings = rule_analyzer.analyze([f])
        sec_findings = [x for x in findings if x.rule == "security/hardcoded-secret"]
        assert sec_findings[0].category == Category.SECURITY


# ─── Rule: quality/long-line ──────────────────────────────────────────────────

class TestLongLine:
    def test_fires_on_121_char_line(self):
        long_line = "x = " + "a" * 117  # 4 + 117 = 121 chars
        f = make_file("utils.py", [long_line])
        findings = rule_analyzer.analyze([f])
        assert "quality/long-line" in get_rule_ids(findings)

    def test_no_fire_on_120_char_line(self):
        line_120 = "x = " + "a" * 116  # 4 + 116 = 120 chars exactly
        f = make_file("utils.py", [line_120])
        findings = rule_analyzer.analyze([f])
        assert "quality/long-line" not in get_rule_ids(findings)

    def test_fires_on_very_long_line(self):
        very_long = "a" * 200
        f = make_file("utils.py", [very_long])
        findings = rule_analyzer.analyze([f])
        assert "quality/long-line" in get_rule_ids(findings)

    def test_severity_is_low(self):
        long_line = "x = " + "a" * 117
        f = make_file("utils.py", [long_line])
        findings = rule_analyzer.analyze([f])
        long_findings = [x for x in findings if x.rule == "quality/long-line"]
        assert long_findings[0].severity == Severity.LOW


# ─── General analyzer behaviour ───────────────────────────────────────────────

class TestAnalyzerGeneral:
    def test_skips_binary_files(self):
        cf = ChangedFile(
            filename="image.png",
            status="added",
            additions=0,
            deletions=0,
            hunks=[],
            is_binary=True,
            has_patch=False,
        )
        findings = rule_analyzer.analyze([cf])
        assert findings == []

    def test_skips_files_without_patch(self):
        cf = ChangedFile(
            filename="large_file.csv",
            status="modified",
            additions=100,
            deletions=50,
            hunks=[],
            is_binary=False,
            has_patch=False,
        )
        findings = rule_analyzer.analyze([cf])
        assert findings == []

    def test_multiple_rules_fire_on_same_file(self):
        """A file can trigger multiple different rules simultaneously."""
        f = make_file(
            "bad.py",
            [
                'password = "hardcodedpass"',
                "print(password)",
                "# TODO: hash this",
            ],
        )
        findings = rule_analyzer.analyze([f])
        rule_ids = get_rule_ids(findings)
        assert "security/hardcoded-secret" in rule_ids
        assert "debug/print-statement" in rule_ids
        assert "quality/todo" in rule_ids

    def test_finding_has_correct_file(self):
        f = make_file("mymodule/service.py", ["console.log('x')"])
        # Override to JS for console.log test
        f_js = make_file("mymodule/service.js", ["console.log('x')"])
        findings = rule_analyzer.analyze([f_js])
        assert findings[0].file == "mymodule/service.js"

    def test_finding_has_correct_line_number(self):
        lines = ["x = 1", "console.log(x)", "y = 2"]
        f = make_file("app.js", lines)
        findings = rule_analyzer.analyze([f])
        console_findings = [x for x in findings if x.rule == "debug/console-log"]
        # console.log is on line 2 (1-indexed)
        assert console_findings[0].line == 2

    def test_finding_source_is_static(self):
        f = make_file("app.js", ["console.log('x')"])
        findings = rule_analyzer.analyze([f])
        assert all(x.source == "static" for x in findings)

    def test_empty_pr_returns_no_findings(self):
        assert rule_analyzer.analyze([]) == []
