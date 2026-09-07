# AI CodeReview — Interview Preparation

## Resume bullets

- Built a FastAPI + React pull-request review application that validates public GitHub PR URLs, fetches metadata and changed-file patches through the GitHub REST API, and returns structured review results to a browser UI.
- Combined deterministic added-line checks (`console.log`, `print`, TODO/FIXME, likely secrets, long lines) with Gemini-based semantic review for potential logic, error-handling, performance, and maintainability concerns.
- Designed a strict LLM response contract with Pydantic enums and strict scalar fields; malformed or schema-invalid Gemini output receives one corrective format request before a controlled API failure.
- Added practical security and quality controls: GitHub-only URL allowlisting, untrusted-diff prompt boundaries, no code execution, bounded file/diff/model input sizes, mocked external-service tests, and a 12-case offline evaluation fixture set.

## What you genuinely built

- A synchronous FastAPI API with `fetch-pr` and `analyze` endpoints, a React UI, and Docker Compose packaging.
- Public GitHub PR metadata and file-patch retrieval using two read-only REST endpoints. It fetches only the first page of up to 100 files, then processes at most 50 files.
- A lightweight unified-diff parser, regex rules, a Gemini 1.5 Flash integration, and a `ReviewService` that combines the results.
- Pydantic validation, one correction retry, safe HTTP error mapping, and warnings for capped files/diffs/model input.
- 74 mocked/offline pytest tests and a 12-case fixture evaluator. The current checked-in evaluation report scores deterministic rules only; **no recorded live LLM outputs have been evaluated yet**.

## BASIC

### 1. What problem does the project solve?

- **Testing:** Can you define the user value precisely?
- **Strong answer:** It gives developers an initial, read-only review of a public GitHub PR. Deterministic rules catch literal patterns quickly, while Gemini looks for reasoning-level concerns in the diff. The output is a structured suggestion for a human reviewer, not a merge decision.
- **Simple explanation:** It saves time finding obvious and potentially subtle review concerns.
- **Follow-ups:** What can it not know? Why not auto-approve?
- **Avoid:** “It guarantees bug-free code.”

### 2. Why did you build it?

- **Testing:** Whether the design choices follow a real problem.
- **Strong answer:** I wanted to show the complementary roles of deterministic checks and LLM reasoning, while treating model output and repository text as untrusted external input.
- **Simple explanation:** Rules are predictable; an LLM adds code-understanding signals.
- **Follow-ups:** Why not only use a linter?
- **Avoid:** “LLMs replace reviewers.”

### 3. Explain the architecture.

- **Testing:** System decomposition.
- **Strong answer:** React calls FastAPI through one API service. The router delegates to `ReviewService`, which coordinates GitHub retrieval, diff parsing, rule analysis, Gemini, validation/retry, deduplication, and response shaping. Each external boundary has its own service or schema.
- **Simple explanation:** UI, orchestration, external APIs, parsing, rules, and validation have separate jobs.
- **Follow-ups:** Why is `ReviewService` central?
- **Avoid:** Calling it microservices; it is one application.

### 4. Walk through a complete request.

- **Testing:** End-to-end understanding.
- **Strong answer:** The user posts a GitHub PR URL. The backend validates it, builds fixed GitHub API URLs, fetches PR metadata and files, bounds the input, parses patches, runs rules, sends bounded review context to Gemini, validates its JSON with at most one repair, merges/deduplicates findings, and returns metadata, warnings, review, and a text diff preview.
- **Simple explanation:** Fetch, filter, inspect, reason, validate, return.
- **Follow-ups:** Where can the request fail?
- **Avoid:** Saying code is cloned or executed—it is not.

## GITHUB

### 5. How does GitHub PR fetching work?

- **Testing:** API integration details.
- **Strong answer:** `github_service` extracts owner, repo, and PR number, then uses `httpx` to GET `/repos/{owner}/{repo}/pulls/{number}` and `/files` from `https://api.github.com`. It sends optional bearer auth, uses a timeout, and maps expected HTTP failures to typed errors.
- **Simple explanation:** Two read-only API calls provide PR details and patches.
- **Follow-ups:** Pagination? Answer: it requests `per_page=100` but does not paginate further.
- **Avoid:** Claiming all changed files are fetched.

### 6. How do you parse a PR URL?

- **Testing:** Input validation and SSRF awareness.
- **Strong answer:** `urlparse` requires HTTPS, hostname exactly `github.com`, and no embedded credentials. A full-match regex accepts `/owner/repo/pull/positive-number`, with an optional trailing slash. The submitted URL is never fetched directly.
- **Simple explanation:** Only a real GitHub PR-shaped URL is accepted.
- **Follow-ups:** What about `github.com.evil.com`? It fails hostname validation.
- **Avoid:** “A substring check is enough.”

### 7. What is a Git diff?

- **Testing:** Core data-model knowledge.
- **Strong answer:** A unified diff represents changes in hunks. `@@ -old +new @@` gives ranges; `+` lines are additions, `-` removals, and space-prefixed lines are unchanged context. The parser tracks line numbers so findings can point to new code.
- **Simple explanation:** It is a compact before/after representation of file changes.
- **Follow-ups:** Why inspect added lines for rules?
- **Avoid:** Saying it contains the entire repository.

### 8. What happens if GitHub API fails?

- **Testing:** Error handling.
- **Strong answer:** Invalid URLs become 422, missing/private PRs 404, and GitHub failures/timeouts 502 with safe messages. The pipeline stops before parsing or Gemini.
- **Simple explanation:** A failed fetch cannot produce a review.
- **Follow-ups:** How would you improve rate-limit handling?
- **Avoid:** Exposing raw upstream responses to browsers.

### 9. Why didn't you use OAuth?

- **Testing:** Scope judgment.
- **Strong answer:** The implemented scope is public PRs with an optional server-side token to improve quota. OAuth would require user identity, authorization callback handling, token storage, refresh/revocation, and a private-repo permission model, none of which this project implements.
- **Simple explanation:** OAuth was deliberately out of scope.
- **Follow-ups:** What would change for private repositories?
- **Avoid:** Claiming private PR support.

## CODE ANALYSIS

### 10. What checks are deterministic?

- **Testing:** Specific knowledge.
- **Strong answer:** The current regex rules flag `console.log`, Python `print`, Java `System.out.println`, TODO/FIXME/HACK/XXX markers, likely hardcoded credentials, and added lines over 120 characters.
- **Simple explanation:** These are literal patterns where consistent detection is useful.
- **Follow-ups:** Which source/severity do they receive?
- **Avoid:** Including logic-bug detection in the rule list.

### 11. Why use regex?

- **Testing:** Trade-off reasoning.
- **Strong answer:** Regex is fast, cheap, transparent, deterministic, and easy to unit test. It is a good fit for literal added-line patterns, not semantic program analysis.
- **Simple explanation:** It reliably spots text patterns without model cost.
- **Follow-ups:** False positives for comments or strings?
- **Avoid:** “Regex understands code flow.”

### 12. What are the limitations?

- **Testing:** Intellectual honesty.
- **Strong answer:** Rules can match harmless text and miss equivalent patterns; the parser is deliberately lightweight; only diffs—not whole repositories—are reviewed; the first 50 files and bounded content are processed; and no later GitHub pages are fetched.
- **Simple explanation:** It favors predictable bounds over complete repository understanding.
- **Follow-ups:** How would you prioritize files later?
- **Avoid:** Claiming complete static analysis.

### 13. Why not use a complete static analyzer?

- **Testing:** Scope and tooling trade-offs.
- **Strong answer:** A complete analyzer needs language-specific parsers, builds, dependency setup, rulesets, and often repository context. This project intentionally uses a small cross-language rule layer plus an LLM for review reasoning.
- **Simple explanation:** Full static analysis is much broader than parsing a PR patch.
- **Follow-ups:** What would you add for Python? Ruff/Bandit, but they are not implemented.
- **Avoid:** Claiming Gemini is a static analyzer.

## LLM

### 14. Why use an LLM?

- **Testing:** Appropriate model use.
- **Strong answer:** The LLM is for issues requiring contextual reasoning: potentially inverted conditions, missing handling, suspicious flow, or maintainability concerns. It complements—not replaces—the deterministic rules.
- **Simple explanation:** It can interpret relationships that a regex cannot.
- **Follow-ups:** Why not trust it blindly?
- **Avoid:** “It understands the entire system.”

### 15. Why Gemini?

- **Testing:** Concrete implementation awareness.
- **Strong answer:** The implementation uses the Google Generative AI SDK and configures `gemini-1.5-flash`. It was a practical API integration choice; this repository does not include comparative benchmark results against other models.
- **Simple explanation:** It is the model API wired into this project.
- **Follow-ups:** How would you select a model scientifically?
- **Avoid:** Unsupported quality or cost claims.

### 16. What does the prompt contain?

- **Testing:** Data flow and privacy awareness.
- **Strong answer:** The system instruction contains trusted review policy and strict output rules. User content contains bounded PR title/description, static findings, and parsed diff text with file/hunk/line information. Metadata is capped at 8,000 characters and diff input at 40,000.
- **Simple explanation:** Policy stays separate from the PR data being reviewed.
- **Follow-ups:** Is the PR description trusted? No.
- **Avoid:** Saying it sends full repository contents.

### 17. How do you prevent prompt injection?

- **Testing:** Security realism.
- **Strong answer:** I separate developer instructions using Gemini's `system_instruction`, label PR text/diff as untrusted, delimit it, repeat that comments/strings are data rather than commands, and never execute code. This mitigates injection; it does not make LLM prompt injection impossible.
- **Simple explanation:** The model is told which instructions count and which text is only code to inspect.
- **Follow-ups:** What is the residual risk?
- **Avoid:** “Prompt injection is solved.”

### 18. Why shouldn't code comments be trusted?

- **Testing:** Threat modeling.
- **Strong answer:** Comments are contributor-controlled text and can embed directives such as “ignore prior instructions.” They must be reviewed as data just like string literals or variable names.
- **Simple explanation:** A comment can be malicious text, not documentation.
- **Follow-ups:** What else is untrusted? PR title/body and all diff content.
- **Avoid:** Treating comments as system instructions.

## STRUCTURED OUTPUT

### 19. Why JSON?

- **Testing:** Contract design.
- **Strong answer:** JSON gives the frontend stable fields for summary, status, and findings instead of parsing prose. It also permits machine validation and safe rendering of severity/category/file/line/suggestion.
- **Simple explanation:** The UI needs predictable data, not a paragraph to guess at.
- **Follow-ups:** Why isn't “return JSON” alone sufficient?
- **Avoid:** Saying JSON guarantees validity.

### 20. Why Pydantic?

- **Testing:** Defensive programming.
- **Strong answer:** Pydantic checks the response contract at the untrusted model boundary. It enforces required fields, allowed enums, strict strings/integers for findings, and forbids unknown fields. Empty findings are intentionally valid.
- **Simple explanation:** It blocks malformed model output before it reaches React.
- **Follow-ups:** Which values are enums?
- **Avoid:** “The prompt makes validation unnecessary.”

### 21. What happens when the LLM returns invalid JSON?

- **Testing:** Failure-path knowledge.
- **Strong answer:** The service strips a simple markdown fence if present, attempts JSON parse and `ReviewResponse` validation, then sends the validation problem and bad output back once for a structure-only correction.
- **Simple explanation:** It gives a common formatting error one chance to be repaired.
- **Follow-ups:** What errors are caught? JSON decoding and Pydantic validation.
- **Avoid:** Saying it endlessly retries.

### 22. Why only one retry?

- **Testing:** Cost and reliability trade-off.
- **Strong answer:** One retry handles transient formatting mistakes while bounding latency, token usage, and repeated bad outputs. If the model failed twice, more retries are not a reliable recovery strategy in this synchronous request.
- **Simple explanation:** A hard limit prevents a broken request from looping.
- **Follow-ups:** What could a future asynchronous system do?
- **Avoid:** “One retry guarantees success.”

### 23. What if the retry also fails?

- **Testing:** Controlled degradation.
- **Strong answer:** `LLMServiceError` is raised, and the API returns a safe 503 message. It does not return unvalidated content or silently pretend the PR is approved.
- **Simple explanation:** No valid model output means no AI review result.
- **Follow-ups:** Could static findings still be returned? Not in the current implementation; the full request fails.
- **Avoid:** Claiming partial static fallback exists.

## SECURITY

### 24. Can the application execute submitted code?

- **Testing:** Core safety property.
- **Strong answer:** No. It fetches JSON and patch text, parses strings, runs regex, and sends text to Gemini for analysis. It does not clone repositories, invoke interpreters, build code, or run shell commands from a PR.
- **Simple explanation:** Code is read as text only.
- **Follow-ups:** What about a malicious `package.json`? It is still only text.
- **Avoid:** “The LLM executes it mentally.”

### 25. How are API keys protected?

- **Testing:** Client/server boundary.
- **Strong answer:** Keys are backend settings from environment variables or `.env`; React never receives them. Docker Compose injects backend environment variables and `.dockerignore` excludes `.env`. A `VITE_` prefixed key would be unsafe and is not used.
- **Simple explanation:** Browsers only receive review data, never secret credentials.
- **Follow-ups:** What needs protection in deployment? Secret store/access controls/rotation—outside this repo.
- **Avoid:** Saying `.env` is secure by itself.

### 26. How do you prevent arbitrary URLs from being fetched?

- **Testing:** SSRF defense.
- **Strong answer:** The submitted URL must be HTTPS with hostname exactly `github.com` and an allowed PR path. The service then constructs a request to constant `https://api.github.com`; it never requests the submitted URL.
- **Simple explanation:** User text selects GitHub identifiers, not a network destination.
- **Follow-ups:** Why check username/password in URL? They are rejected.
- **Avoid:** “Regex alone prevents SSRF.”

### 27. What happens with malicious code in a PR?

- **Testing:** Prompt injection response.
- **Strong answer:** It is parsed as diff text, not executed. The LLM prompt calls it untrusted data and tells Gemini not to obey comment/string instructions. It may still receive an analysis result, subject to model limitations and output validation.
- **Simple explanation:** Malicious code cannot run in this application.
- **Follow-ups:** Does this eliminate harmful advice? No.
- **Avoid:** Claiming semantic safety is guaranteed.

## SOFTWARE ENGINEERING

### 28. Why FastAPI?

- **Testing:** Framework fit.
- **Strong answer:** FastAPI provides typed request/response models, automatic validation, clear route definitions, and straightforward integration with Pydantic. The current synchronous services run in FastAPI's thread pool rather than blocking an async event loop directly.
- **Simple explanation:** It makes a typed Python API concise.
- **Follow-ups:** Is the whole implementation async? No.
- **Avoid:** Claiming async throughput measurements.

### 29. Why separate services?

- **Testing:** Maintainability/testability.
- **Strong answer:** GitHub I/O, patch parsing, deterministic rules, Gemini interaction, and orchestration fail differently and can be tested independently. This also lets tests mock only external boundaries.
- **Simple explanation:** One job per service keeps changes localized.
- **Follow-ups:** Why not put it in the route?
- **Avoid:** Saying services are separate deployed microservices.

### 30. Why separate rule-based analysis from LLM analysis?

- **Testing:** Hybrid design.
- **Strong answer:** Rules are deterministic, immediate, and evidence-based for literal patterns. Gemini handles contextual hypotheses. Static findings are supplied to Gemini so it should not duplicate those exact checks, then results are merged and exact location/message duplicates removed.
- **Simple explanation:** Use the reliable tool for literal checks and the flexible tool for reasoning.
- **Follow-ups:** Is deduplication semantic? No, it is exact normalized file/line/message matching.
- **Avoid:** Claiming all duplicate meaning is removed.

### 31. How would you scale this?

- **Testing:** Distinguishing design from implementation.
- **Strong answer:** This code is synchronous and intentionally small. I would first measure GitHub and Gemini latency, add edge rate limits, cache immutable PR revisions, prioritize files by risk, and move long review requests to durable background work only if usage requires it. Those changes are not implemented here.
- **Simple explanation:** Measure first, then decouple slow work when necessary.
- **Follow-ups:** What state would you need for jobs?
- **Avoid:** Claiming it already scales horizontally or uses queues.

### 32. What are the bottlenecks?

- **Testing:** Performance realism.
- **Strong answer:** Network latency to GitHub and Gemini dominates; model inference and large prompt size are likely the main cost/latency drivers. Parsing and regex rules are comparatively small. The current endpoint blocks until all steps finish.
- **Simple explanation:** Waiting for external services is slower than scanning text.
- **Follow-ups:** How would you instrument it?
- **Avoid:** Providing unmeasured timings.

### 33. How would you reduce LLM cost?

- **Testing:** Practical optimization.
- **Strong answer:** The implementation already caps metadata and LLM diff text and runs rules first. Next I would skip low-risk files, send narrower hunk context, cache per commit SHA, use model selection by PR complexity, and measure recall degradation. These next steps are proposals, not current features.
- **Simple explanation:** Send less, better-targeted text and avoid repeat calls.
- **Follow-ups:** What is the trade-off? Missed context/issues.
- **Avoid:** Saying truncation is free of quality loss.

### 34. How would you handle huge PRs?

- **Testing:** Existing limits and future design.
- **Strong answer:** Today it processes the first 50 files, caps total parsed patch content at 200,000 characters, caps Gemini diff input at 40,000 characters, prioritizes changed lines, skips missing-patch/binary details, and returns warnings. A future version could risk-rank files or split-and-aggregate reviews, but it does not implement chunking or queues now.
- **Simple explanation:** It is intentionally partial and tells users when it is partial.
- **Follow-ups:** Is first-file ordering ideal? No; it is a simple deterministic policy.
- **Avoid:** Claiming it reviews any-size PR completely.

## EVALUATION

### 35. How do you know your system works?

- **Testing:** Evidence quality.
- **Strong answer:** There are 74 automated tests for parsing, rules, mocked GitHub mappings, schema validation, retry behavior, orchestration, and limits. The 12-case offline fixture run reports zero false positives/negatives for the deterministic cases. That verifies known behavior, not general correctness.
- **Simple explanation:** Tests prove specific contracts, not every real PR outcome.
- **Follow-ups:** What does the report not test?
- **Avoid:** “The test suite proves the LLM is accurate.”

### 36. What are false positives?

- **Testing:** Evaluation literacy.
- **Strong answer:** A false positive is a finding where the system reports a problem but the code/control case has no real issue. It wastes reviewer attention and can reduce trust.
- **Simple explanation:** A false alarm.
- **Follow-ups:** Which controls help detect it? Clean code, removed debug code, injection-text control.
- **Avoid:** Confusing it with a missed bug.

### 37. What are false negatives?

- **Testing:** Evaluation literacy.
- **Strong answer:** A false negative is a known expected issue that the system misses. It is especially important for high-severity security or correctness review, but reducing it can increase false positives.
- **Simple explanation:** A missed alarm.
- **Follow-ups:** What trade-off does tuning involve?
- **Avoid:** Saying zero fixture misses means zero misses in production.

### 38. How did you evaluate the LLM?

- **Testing:** Honesty about implementation.
- **Strong answer:** I created three LLM-oriented expected cases in the 12-case fixture set and an evaluator that can ingest recorded, human-reviewed LLM results. I have not yet checked in recorded Gemini results, so the current report explicitly marks LLM evaluation as false—not measured. I did test malformed/valid response and retry behavior with a fake Gemini SDK.
- **Simple explanation:** The framework is ready, but model quality has not been benchmarked yet.
- **Follow-ups:** What would you add? Versioned prompts/models, multiple samples, human labels, precision/recall.
- **Avoid:** Claiming LLM precision, recall, or accuracy.

### 39. Why isn't your evaluation perfect?

- **Testing:** Scientific skepticism.
- **Strong answer:** Twelve tiny curated diffs are too small and synthetic to represent languages, repositories, severity judgments, or full application context. LLM outputs vary by model/version and review quality can be subjective. It is a regression signal, not a correctness proof.
- **Simple explanation:** A small quiz cannot measure all real-world review quality.
- **Follow-ups:** How would you make it better?
- **Avoid:** Treating the report as a benchmark.

## Critical questions to practice aloud

1. **Why does the URL validator inspect both `hostname` and path rather than only a regex?**
   - **Testing:** SSRF understanding. **Strong answer:** host allowlisting and fixed API construction prevent user input from selecting arbitrary destinations; the path regex validates identifiers. **Simple:** validate where and what. **Follow-up:** What about redirects? **Wrong:** “The frontend validation protects the backend.”

2. **Why does the current output deduplicator not remove semantically similar findings?**
   - **Testing:** Code-level accuracy. **Strong answer:** it keys only normalized file, line, and message to avoid unsafe fuzzy collapsing. **Simple:** only identical location/message is removed. **Follow-up:** How could you improve it? **Wrong:** “It uses embeddings.”

3. **What happens when a PR has 200 files?**
   - **Testing:** Limits. **Strong answer:** GitHub `/files` is requested for up to 100 on one page, then the reviewer uses at most the first 50 returned; it warns about its 50-file processing cap. **Simple:** it does not fully review 200 files. **Follow-up:** Why is that a limitation? **Wrong:** “All 200 are analyzed.”

4. **Does one correction retry retry the original Gemini request?**
   - **Testing:** Retry implementation. **Strong answer:** no; after validation fails, it starts a chat, sends the original prompt for context, and then sends a correction prompt containing the error/bad response. **Simple:** it asks the model to repair its output format once. **Follow-up:** What if Gemini network call fails? **Wrong:** “It retries indefinitely.”

5. **What is the difference between static and LLM test confidence?**
   - **Testing:** Evaluation honesty. **Strong answer:** static patterns have repeatable fixtures and the current report covers them; LLM output structure is mocked/tested, but quality has no recorded-output score yet. **Simple:** we tested the LLM plumbing more than its review accuracy. **Follow-up:** What would establish quality? **Wrong:** “The schema proves it.”

6. **Why do binary/no-patch files still appear in the parsed file list?**
   - **Testing:** Data flow. **Strong answer:** they preserve PR metadata but are marked `has_patch=False`; rule analysis skips them and the user receives a warning that detailed analysis was unavailable. **Simple:** visible, but not analyzed as source. **Follow-up:** Could a binary contain a secret? **Wrong:** “They are analyzed normally.”

7. **Could the current API return static results if Gemini is down?**
   - **Testing:** Graceful-degradation accuracy. **Strong answer:** no. `ReviewService` calls Gemini before constructing the final response, so Gemini failure produces a controlled 503. Returning static-only fallback would be a future behavior change. **Simple:** AI outage fails the complete review today. **Follow-up:** Would you change that? **Wrong:** “It automatically falls back.”

8. **Why is line type sorting in LLM formatting a trade-off?**
   - **Testing:** Prompt construction detail. **Strong answer:** changed lines appear first, helping truncation retain the code under review, but reordered hunk lines can reduce natural reading flow. It is a simple prioritization, not perfect context selection. **Simple:** better coverage of changes, slightly less narrative order. **Follow-up:** How would you improve it? **Wrong:** “It preserves exact diff order.”
