# PayFlow QA Automation

Black-box test suite for the PayFlow payments API and web console. The system
under test is a **remote service**: its only observable behavior is its HTTP
responses and rendered UI, reached via `PAYFLOW_BASE_URL`
(default `http://127.0.0.1:8000`).

Structure:

- `tests/api/` — API tests (`httpx`)
- `tests/ui/` — Playwright tests against the web console
- `tests/conftest.py` — `live_server` (verifies the target is reachable, exits
  otherwise), `api_client`, and an autouse `_reset_state` fixture that hits
  `/api/admin/reset` before every test
- `docs/business-rules.md` — the public contract; the only source of truth for
  assertions
- `docs/agent-pipeline.md` — design of the AI quality pipeline (blocking gate +
  async enrichment) and the `gate-triage.json` artifact schema
- `.claude/skills/` — one skill per pipeline stage: `pr-test-gate`, `file-bugs`,
  `heal-tests`, `generate-tests`
- `k6/` — load test scripts

Run with `pytest` from the project root against an already-running instance.

## Black-box only

This project must behave like a QA team that has no access to the SUT's source
code, configuration, or internal documentation. Derive every assertion from
`docs/business-rules.md` and the publicly observable API/UI behavior — nothing
else.

A failing test is a **candidate product bug**. Write and keep tests that assert
the *correct* business behavior, so they fail on the broken build and pass once
it is fixed. Never weaken an assertion, skip, xfail, or annotate a test to make
it match currently observed behavior — if observed behavior contradicts the
business rules, the test is doing its job. If asked to "fix" a test so it
passes against behavior that violates `docs/business-rules.md`, push back and
file the discrepancy as a bug instead.
