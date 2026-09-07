"""
services/rule_analyzer.py — deterministic, regex-based code checks.

Deterministic vs Probabilistic analysis — interview explanation:
────────────────────────────────────────────────────────────────
  Deterministic: Given the same input, always produces the same output.
  These rules are pure functions — no randomness, no model inference.
  They are fast (microseconds), free (no API call), and 100% explainable.

  Probabilistic: An LLM may produce different output for the same input
  on different runs.  It is more powerful for semantic reasoning ("is
  this logic correct?") but cannot reliably catch exact pattern matches
  as efficiently as a regex.

Why handle these rules WITHOUT an LLM:
  1. Speed  — regex runs in microseconds; an LLM call takes 1–3 seconds.
  2. Cost   — every LLM call costs tokens; these checks cost nothing.
  3. Reliability — LLMs can miss obvious patterns; regex never will.
  4. Explainability — you can point to the exact line that matched.

Limitations of regex-based checks (be honest in interviews!):
  - Regex cannot understand context. A print() inside a comment will
    still trigger the debug-statement rule.
  - Regex cannot catch logic bugs, race conditions, or design problems.
  - A hardcoded password regex has false positives (e.g. test fixtures).
  - This is NOT a replacement for tools like Semgrep, Bandit, or ESLint.

We only claim: "these rules catch a well-defined, limited set of obvious
issues reliably and cheaply."
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.diff import ChangedFile, DiffLine, LineType
from app.schemas.review import Category, Finding, Severity


# ─── Rule definitions ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Rule:
    """
    A single rule definition.  frozen=True makes it hashable and
    prevents accidental mutation after creation.
    """
    id: str
    pattern: re.Pattern[str]
    severity: Severity
    category: Category
    message: str
    suggestion: str


# We compile patterns once at import time for efficiency.
RULES: list[Rule] = [
    # ── Debug statements ─────────────────────────────────────────────────────
    Rule(
        id="debug/console-log",
        pattern=re.compile(r"\bconsole\.log\s*\("),
        severity=Severity.LOW,
        category=Category.QUALITY,
        message="console.log() left in production code.",
        suggestion="Remove or replace with a proper logging library (e.g. winston, loglevel).",
    ),
    Rule(
        id="debug/print-statement",
        pattern=re.compile(r"\bprint\s*\("),
        severity=Severity.LOW,
        category=Category.QUALITY,
        message="print() statement left in production code.",
        suggestion="Remove or replace with Python's logging module (logging.debug / logging.info).",
    ),
    Rule(
        id="debug/system-out-println",
        pattern=re.compile(r"\bSystem\.out\.println\s*\("),
        severity=Severity.LOW,
        category=Category.QUALITY,
        message="System.out.println() left in production code.",
        suggestion="Use a proper Java logger (java.util.logging, Log4j, SLF4J).",
    ),

    # ── Technical debt markers ────────────────────────────────────────────────
    Rule(
        id="quality/todo",
        pattern=re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE),
        severity=Severity.LOW,
        category=Category.MAINTAINABILITY,
        message="TODO/FIXME comment found — unfinished work left in code.",
        suggestion="Resolve the TODO before merging, or create a tracked issue and link it here.",
    ),

    # ── Security: obvious hardcoded secrets ──────────────────────────────────
    # This pattern looks for: password/secret/api_key/token = "literal_value"
    # It deliberately requires a string literal on the right side to reduce
    # false positives (e.g. `password = get_env("PASSWORD")` is fine).
    Rule(
        id="security/hardcoded-secret",
        pattern=re.compile(
            r'(?i)(password|passwd|secret|api_key|apikey|token|auth_token|access_key)\s*'
            r'[=:]\s*["\'][^"\']{4,}["\']'
        ),
        severity=Severity.CRITICAL,
        category=Category.SECURITY,
        message="Possible hardcoded secret or credential detected.",
        suggestion=(
            "Never hardcode credentials. Use environment variables or a secrets manager "
            "(e.g. python-dotenv, AWS Secrets Manager, Vault)."
        ),
    ),

    # ── Long lines ───────────────────────────────────────────────────────────
    # Checked separately because it uses len() rather than regex match content.
    # We define the rule here for consistency; the analyzer handles it specially.
    Rule(
        id="quality/long-line",
        pattern=re.compile(r".{121,}"),   # 121+ chars → over 120 limit
        severity=Severity.LOW,
        category=Category.MAINTAINABILITY,
        message="Line exceeds 120 characters.",
        suggestion="Break the line into multiple shorter lines for readability.",
    ),
]

# Build a quick lookup by ID
RULE_MAP: dict[str, Rule] = {r.id: r for r in RULES}


# ─── Analyzer ─────────────────────────────────────────────────────────────────

class RuleBasedAnalyzer:
    """
    Runs all deterministic rules against the added lines of each changed file.

    Key design choice: we only analyze ADDED lines, not context or removed lines.
    Rationale: flagging removed code would be noise — it's already being deleted.
    We only care about new problems being introduced by this PR.
    """

    def analyze(self, changed_files: list[ChangedFile]) -> list[Finding]:
        """
        Run all rules against every changed file.
        Returns a flat list of Finding objects.
        """
        findings: list[Finding] = []

        for changed_file in changed_files:
            if not changed_file.has_patch or changed_file.is_binary:
                # No patch → nothing to analyze
                continue

            file_findings = self._analyze_file(changed_file)
            findings.extend(file_findings)

        return findings

    def _analyze_file(self, changed_file: ChangedFile) -> list[Finding]:
        """Run all rules against the added lines of a single file."""
        findings: list[Finding] = []

        # We only inspect added lines — new code being introduced.
        for line in changed_file.added_lines:
            for rule in RULES:
                if rule.pattern.search(line.content):
                    finding = Finding(
                        severity=rule.severity,
                        category=rule.category,
                        file=changed_file.filename,
                        line=line.new_lineno,
                        message=rule.message,
                        suggestion=rule.suggestion,
                        rule=rule.id,
                        source="static",
                    )
                    findings.append(finding)
                    # One rule match per line is enough —
                    # break to avoid duplicate findings for the same line + rule.
                    # (A line could match multiple different rules though, which is fine.)

        return findings


# Module-level singleton — one analyzer instance shared by the whole app.
rule_analyzer = RuleBasedAnalyzer()
