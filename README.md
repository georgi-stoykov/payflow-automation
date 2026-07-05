# PayFlow QA Automation

Black-box automated test suite for the PayFlow payments gateway (API + web
console), plus k6 load tests. The suite knows nothing about the SUT's
internals — it targets a running instance over HTTP only.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

## Running

Point the suite at a running PayFlow instance (defaults to
`http://127.0.0.1:8000`):

```bash
pytest                                   # api + ui tests
PAYFLOW_BASE_URL=http://host:port pytest # other environment
k6 run k6/quote_payment_load.js          # load test (BASE_URL env var)
```

If the target is not reachable, the run aborts immediately with a message
instead of starting anything itself.

Useful selections (markers registered in `pytest.ini`):

```bash
pytest -m "not slow"                 # skip real-time waits (quote expiry etc.)
pytest -m "payments or idempotency"  # one functional area
SMOKE=1 k6 run k6/quote_payment_load.js  # short CI-friendly load profile
```

## Layout

- `tests/api/` — API tests: quotes, payments, idempotency, pagination
- `tests/ui/` — Playwright tests for the payment flow in the web console
- `docs/business-rules.md` — the public contract all assertions derive from
- `docs/test-selection.md` — diff → test-subset rules used by the CI quality gate
- `docs/bug-log.md` — candidate product bugs the suite currently flags
- `.claude/skills/pr-test-gate/` — instructions for the AI agent that gates PRs
- `k6/` — load test scripts

## AI quality gate

PRs on the PayFlow sandbox repo trigger a GitHub Actions workflow in which a
Claude agent reads the diff, picks the relevant subset of this suite via
`docs/test-selection.md`, runs it against the PR's build, triages every failure
against `docs/business-rules.md` (product bug / test defect / environment), and
posts the report on the PR. The agent may never weaken a test to get to green.

## Philosophy

Strictly black-box: assertions come from `docs/business-rules.md` and observed
public behavior, never from the SUT's implementation. A red test asserting a
documented business rule is a bug report, not a test defect — see `CLAUDE.md`.
