# Risk-based test selection rules

Maps areas of change in a PayFlow PR to the test subset that must run. Used by the
AI quality gate in CI and by humans running the suite selectively. Selection is by
pytest marker (`-m`), registered in `pytest.ini`.

## Principles

1. **Fail open to more testing.** If the diff is unclear, mixed, or touches shared
   code, run the **full suite**. Never fail open to less.
2. **Always** include a happy-path test for every touched area, even for
   "refactor only" claims.
3. `slow` tests (real waits: quote expiry, lifecycle timing) are included when the
   diff touches timing/expiry/lifecycle logic; otherwise they may be excluded with
   `-m "<selection> and not slow"` to keep the gate fast.
4. k6 smoke (`SMOKE=1 k6 run k6/quote_payment_load.js`) runs when the diff touches
   the hot path: quote or payment creation, or anything on the request path
   (routing, middleware, serialization).

## Mapping

| Change area (keywords / paths in the SUT diff) | pytest selection | k6 smoke |
|---|---|---|
| Quote logic: pricing, rate, fee, expiry, currencies | `-m quotes` + `-m ui` quote tests | yes |
| Payment creation, lifecycle, status, webhooks | `-m "payments or idempotency"` (include `slow` if timing/lifecycle touched) | yes |
| Idempotency handling | `-m idempotency` | yes |
| KYC / customers | `-m "kyc or payments"` | no |
| Pagination / list endpoints | `-m pagination` | no |
| Web console: templates, static assets, frontend JS | `-m ui` | no |
| Validation / schemas / error handling | `-m "quotes or payments"` | no |
| Dependencies, config, middleware, app startup, unclear or mixed diff | **full suite** (`pytest`) | yes |
| Docs/comments-only diff (verify nothing else changed) | health check + `-m "quotes and not slow"` happy-path smoke | no |

## Reporting expectations

Whatever the selection, the gate report must state:
- which rule(s) matched and why (name the diff files/areas),
- the exact commands run,
- results, with every failure triaged per `docs/business-rules.md`
  (see the pr-test-gate skill).
