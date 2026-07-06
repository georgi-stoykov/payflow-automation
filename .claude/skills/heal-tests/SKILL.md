---
name: heal-tests
description: Repair test-defect and environment failures from a gate run — mechanics only (locators, waits, fixtures, plumbing), never assertions — and open the fix as a PR for human review. Use after a pr-test-gate run that reports test defects.
---

# Test healer

You repair the *mechanics* of failing tests after a gate run. Inputs:
`gate-triage.json` and `gate-report.md` (schema: `docs/agent-pipeline.md`), a
running PayFlow instance, and a writable checkout of this test repo. The
invoker tells you the branch name and target repo for the PR.

## What is (and is not) a heal

A heal changes **how a test reaches the behavior**, never **what it asserts**.

In scope: rotted selectors (prefer accessibility semantics — role, label,
visible text — which stay stable even in chaos mode), timing and waits, fixture
and client plumbing, request shapes **verified against the live API's public
behavior**, flaky setup.

Out of scope: expected status codes, expected values, business-rule logic,
deleting or skipping a test, `xfail`, loosening a comparison. If the only way
to make a test pass is to change what it asserts, it is NOT a heal — stop and
report it for human review (it is likely a product bug or a spec question).

## Procedure

1. Read `gate-triage.json`; act on `failures[]` entries with
   `category == "test-defect"` or `"environment"`.
2. **Reproduce** each failure with a targeted pytest run before touching code.
3. **Diagnose**: mechanics or assertion-level? Probe the live SUT (API
   responses, rendered UI) to confirm — does the element exist under a semantic
   locator? Does the endpoint answer in the documented shape?
4. **Fix mechanics only**, matching the style of the surrounding tests.
5. **Verify**: re-run the affected tests. A heal must turn its failure green or
   expose a cleaner product-bug signal; otherwise revert it.
6. **Open a PR** on the test repo (branch and repo from the invoker, label
   `ai-heal`): configure a bot git identity, commit per healed test file, and
   write a PR body listing, per test: the failure, the diagnosis, and why the
   fix is mechanics-only.
7. Anything you could not heal: list it in the PR body (or the run summary if
   no PR was needed) as needing human review, with your reasoning.

## Hard rules

- Never change an assertion, skip, xfail, or delete a test. A weakened
  assertion is the one unforgivable failure mode of this stage.
- Never merge your own PR; a human reviews every heal.
- Derive expected behavior from `docs/business-rules.md` and publicly
  observable SUT behavior only — never from the SUT diff or source.
