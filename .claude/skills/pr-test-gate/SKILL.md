---
name: pr-test-gate
description: Run the AI quality gate for a PayFlow PR — select tests from the diff, run them, triage failures, and write a gate report. Use when asked to evaluate a PR's changes against the black-box test suite.
---

# PR test gate

You are the quality gate for a PayFlow pull request. You receive a diff summary of
the PR (file list + stat; you may also read the diff itself). The PayFlow instance
built from the PR is already running; `PAYFLOW_BASE_URL` points at it.

## Procedure

1. **Understand the change.** Read the provided diff summary. Identify which
   functional areas it touches (quotes/pricing, payments/lifecycle, idempotency,
   KYC, pagination, web console, infra/config) and which rules in
   `docs/business-rules.md` it implicates. Implicated rules with no covering
   test in the suite become `coverage_gaps` in the machine artifact (step 5).
2. **Select tests** using `docs/test-selection.md`. State which rule(s) matched and
   why before running anything. If the diff is unclear or touches shared/infra code,
   select the **full suite** — when in doubt, run more, never less.
3. **Run** the selection from the test repo root, e.g.:
   - `python -m pytest -m "payments or idempotency" -q`
   - UI tests need Playwright chromium installed; include them per the rules.
   - If the rules call for it: `SMOKE=1 k6 run k6/quote_payment_load.js`
4. **Triage every failure** into exactly one category, judging strictly against
   `docs/business-rules.md`:
   - **Product bug** — observed behavior contradicts a documented business rule.
     Quote the rule. This should FAIL the gate.
   - **Test defect** — the assertion misreads the contract. Report it; do NOT edit
     the test inside the gate run.
   - **Environment** — SUT unreachable, timeout, infra flake. Retry once; if it
     persists, fail the gate as "environment" so a human looks.
5. **Write the report** to `gate-report.md` in the working directory:
   - selection rationale (rules matched, diff areas),
   - exact commands run,
   - pass/fail counts,
   - one triage entry per failure: category, the business rule involved, evidence
     (request/response or UI observation), suggested severity.

   Also write `gate-triage.json` next to it — the machine-readable artifact the
   downstream stages (file-bugs, heal-tests, generate-tests) consume. Schema:
   `docs/agent-pipeline.md`. It repeats the triage in structured form and adds
   `coverage_gaps` (implicated rules with no covering test in the suite).
6. **Write the verdict** to `gate-verdict.txt`: the single word `pass` or `fail`.
   The gate fails if any selected test failed for product-bug or environment
   reasons. Test-defect-only failures still fail the gate (a human must confirm
   the reclassification — the agent must not wave its own suite through).

## Hard rules

- Never edit, skip, xfail, or weaken a test to make it pass. A red test asserting a
  documented rule is the desired signal.
- Never derive assertions from the SUT's source; the diff is used only to *select*
  tests, the contract in `docs/business-rules.md` decides *correctness*.
- Keep output small: summarize, don't paste full tracebacks into the PR comment —
  link the workflow run instead.
