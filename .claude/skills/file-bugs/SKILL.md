---
name: file-bugs
description: Turn the product-bug entries of a gate run's gate-triage.json into deduplicated GitHub issues on the PayFlow SUT repo. Use after a pr-test-gate run whose triage contains product bugs.
---

# Bug filer

You file candidate product bugs found by the PR test gate as GitHub issues on
the SUT repository. The invoker tells you the target repo, the PR number, and
the gate run URL. Inputs: `gate-triage.json` (schema:
`docs/agent-pipeline.md`) and `gate-report.md` from the same gate run.

## Procedure

1. Read `gate-triage.json`. Act only on `failures[]` entries with
   `category == "product-bug"`. Test defects and environment failures are the
   heal stage's job — skip them.
2. **Group** entries that violate the same business rule with the same observed
   behavior into one bug (e.g. several currency-pair tests failing the same
   validation rule are one issue, listing all failing tests).
3. **Dedup before creating anything.** List open candidate bugs:
   `gh issue list -R <repo> --label candidate-bug --state open --json number,title,body`.
   A duplicate = same violated rule and same observed behavior. For a
   duplicate, add a comment linking the new PR and gate run instead of opening
   a new issue.
4. **Ensure labels exist** (`gh label create <name> -R <repo> --force`):
   `candidate-bug`, `ai-quality-gate`, `severity:high`, `severity:medium`,
   `severity:low`.
5. **Create one issue per bug**:
   - title: `[<area>] <one-line observed behavior>`;
   - body: the violated rule quoted from `docs/business-rules.md`, the observed
     behavior with evidence (request → response, or UI observation), the
     failing test ids, severity with a one-line justification, and links to
     the PR and the gate run;
   - labels: `candidate-bug`, `ai-quality-gate`, `severity:<level>`.
6. Print a summary: issues created, duplicates commented on, entries skipped.

## Hard rules

- Report observable behavior only — never speculate about the SUT's source
  code or internals; this is a black-box pipeline.
- Never close, edit, or relabel existing issues; for duplicates, comment only.
- One rule violation = one issue, however many tests detect it.
- No secrets, tokens, or full tracebacks in issue bodies.
