# AI quality pipeline

How the agentic QA workflow around this suite is put together. The pipeline has
two halves with different contracts:

- a **blocking gate** on every SUT pull request — fast, decides merge, runs only
  the existing human-trusted suite;
- **async enrichment** jobs downstream of the gate — non-blocking, they turn the
  gate's triage into GitHub issues and reviewable PRs against this repo.

Agents never merge what they produce, and the gate never counts tests generated
in the same pipeline run. Only the `gate` job may be a required status check.

```
SUT PR ──► understand ──► select ──► run ──► triage ──► report + verdict (blocks merge)
                                               │
                                               ├─► product bugs   ─► file-bugs      ─► GitHub issues (SUT repo)
                                               ├─► test defects   ─► heal-tests     ─► fix PR (this repo, human-reviewed)
                                               └─► coverage gaps  ─► generate-tests ─► candidate-tests PR (this repo, human-reviewed)
```

## Stages

| Stage | Where | Trigger | Consumes | Produces |
|---|---|---|---|---|
| `pr-test-gate` | SUT repo CI, **blocking** | PR opened/updated; push to `main` (post-merge verification) | SUT diff, `docs/test-selection.md`, `docs/business-rules.md` | `gate-report.md`, `gate-verdict.txt`, `gate-triage.json`, PR comment (or run summary on `main` pushes) |
| `file-bugs` | SUT repo CI, non-blocking | gate finished | `gate-triage.json` — `product-bug` entries | deduplicated GitHub issues on the SUT repo |
| `heal-tests` | SUT repo CI, non-blocking | gate finished | `gate-triage.json` — `test-defect` / `environment` entries | mechanics-only fix PR on this repo (branch `ai-heal/pr-<n>`, or `ai-heal/main-<run-id>` for `main`-push runs) |
| `generate-tests` | SUT repo CI, non-blocking | gate finished | `gate-triage.json` — `coverage_gaps` | candidate-tests PR on this repo (branch `ai-tests/pr-<n>`, or `ai-tests/main-<run-id>` for `main`-push runs) |

Each stage has a skill under `.claude/skills/<stage>/SKILL.md`. The skill is the
*process*; this document, `docs/test-selection.md`, and `docs/business-rules.md`
are the *knowledge*. Keep that line clean — it is what makes the process
portable to another project.

## The artifact chain

Every stage consumes the previous stage's artifact and produces its own, so each
step is auditable and re-runnable in isolation:

impact assessment → selection → run results → triage → (issues | heal PR | tests PR)

The chain is carried by one file the gate writes: **`gate-triage.json`**.

### `gate-triage.json` schema (version 1)

```json
{
  "schema": 1,
  "pr": { "repo": "georgi-stoykov/payflow-sandbox", "number": 42, "head_sha": "abc123" },
  "impact": {
    "areas": ["quotes"],
    "risk": "medium",
    "rules_implicated": ["quotes expire 120 seconds after creation"]
  },
  "selection": {
    "selection_rules_matched": ["Quote logic: pricing, rate, fee, expiry, currencies"],
    "pytest_expression": "quotes",
    "k6_smoke": true,
    "commands": ["python -m pytest -m quotes -q"]
  },
  "results": { "passed": 12, "failed": 1, "errors": 0, "skipped": 0 },
  "failures": [
    {
      "test": "tests/api/test_quotes.py::test_quote_rejects_amounts_above_limit",
      "category": "product-bug",
      "rule": "single-payment maximum is 50,000",
      "evidence": "POST /api/quotes amount=50000.01 -> 201 (expected 422)",
      "severity": "high",
      "suggested_action": "file-bug"
    }
  ],
  "coverage_gaps": [
    { "area": "quotes", "rule": "fee is 1.5% of the sell amount", "reason": "no test asserts the fee calculation" }
  ],
  "verdict": "fail"
}
```

Field notes:

- `pr.number` — `0` when the run verifies a push to `main` (post-merge
  verification) rather than a PR; `head_sha` is then the pushed commit.
- `failures[].category` — exactly one of `product-bug`, `test-defect`,
  `environment` (same definitions as the pr-test-gate skill).
- `failures[].rule` — quoted from `docs/business-rules.md`; empty only for
  `environment`.
- `failures[].suggested_action` — `file-bug`, `heal`, or `human-review`.
- `coverage_gaps[]` — business rules implicated by the diff with no covering
  test in the suite; the input to `generate-tests`.
- `evidence` — one line, request/response or UI observation. No tracebacks, no
  secrets.

## Guardrails (non-negotiable)

- **Separation of duties.** The gate judges only the pre-existing, human-trusted
  suite. Generated tests and heals enter via PRs a human approves and take
  effect on *future* gate runs — an agent never grades its own homework.
- **Heals touch mechanics, never assertions** — locators, waits, fixtures,
  request plumbing. If a fix would change *what* a test asserts, it is not a
  heal; it goes back to triage as a product bug or a spec question.
- **Black box.** The SUT diff is used only to select tests and spot coverage
  gaps; `docs/business-rules.md` alone decides correctness.
- **Bugs are filed, not fixed.** No pipeline stage ever edits the SUT.
- **Nothing acts silently.** Every stage that changes something produces a
  reviewable artifact — a report, an issue, or a PR.

## Wiring (CI)

Lives in the SUT repo: `.github/workflows/ai-quality-gate.yml`. Required
secrets there:

- `CLAUDE_CODE_OAUTH_TOKEN` — agent auth (`claude setup-token`); org setups
  would use a managed `ANTHROPIC_API_KEY` instead.
- `QA_REPO_TOKEN` — PAT with write access to **this** repo; lets `heal-tests`
  and `generate-tests` push branches and open PRs here. If unset, those jobs
  skip themselves; the gate and bug filing still run.

Issue and PR conventions:

- Issues (SUT repo): labels `candidate-bug`, `ai-quality-gate`,
  `severity:<high|medium|low>`. Dedup key: violated rule + observed behavior.
  `docs/bug-log.md` is the historical manual log; open issues are the live
  tracker going forward.
- Agent PRs (this repo): labels `ai-heal` / `ai-generated-tests`. The PR body
  must carry the diagnosis (heal) or the rule-to-test traceability table
  (generation).

## Running a stage locally

Any stage can be dry-run from this repo root against a locally running SUT —
invoke the skill (e.g. `/pr-test-gate`) and hand it the same inputs the
workflow passes (diff summary file, `artifacts/` path). Useful for iterating on
a skill without burning CI runs.
