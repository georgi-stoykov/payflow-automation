---
name: generate-tests
description: Generate candidate tests for coverage gaps reported by a gate run and open them as a quarantined PR for human review. Use after a pr-test-gate run whose gate-triage.json lists coverage_gaps.
---

# Test generator

You close coverage gaps: business rules implicated by an SUT change that no
existing test asserts. Inputs: `gate-triage.json` (`coverage_gaps[]`, schema:
`docs/agent-pipeline.md`), `docs/business-rules.md`, a running PayFlow
instance, and a writable checkout of this repo. The invoker tells you the
branch name and target repo for the PR.

## Procedure

1. **Verify each gap.** Grep the suite for the rule first — the gate may have
   missed an existing test. Drop gaps that are already covered and say so.
2. **Write the tests** for real gaps:
   - assertions come from `docs/business-rules.md` only — assert the *correct*
     behavior, even if the current build violates it;
   - match the structure, fixtures, naming, and marker conventions of the
     existing suite (`pytest.ini` markers, `api_client`, autouse
     `_reset_state`);
   - each test's docstring quotes the rule it asserts;
   - place tests in the existing file for their area, or a new
     `tests/api/test_<area>_<topic>.py` if none fits.
3. **Run them** against the live SUT. Each candidate must either pass, or fail
   in a way that matches a documented rule violation (a candidate product bug —
   flag it in the PR so the bug filer or a human picks it up). A test that
   *errors* (typo, broken fixture, wrong URL) gets fixed or dropped — never
   committed red for mechanical reasons.
4. **Open a PR** on the test repo (branch and repo from the invoker, label
   `ai-generated-tests`): configure a bot git identity, commit, push, and write
   a PR body with a traceability table:
   test id → rule quoted → result on this build (pass / candidate bug).
5. These tests take effect only after a human reviews and merges them; they are
   never counted in the gate run that spawned them.

## Hard rules

- Never modify existing tests or shared fixtures in this PR — generation only.
  If a gap requires a fixture change, propose it in the PR body instead.
- Never weaken a candidate to make it pass on the current build.
- Never merge your own PR.
- Black box: the SUT diff told you *where* to look; only
  `docs/business-rules.md` says what is *correct*.
