# Candidate product bugs — current build

Failures observed running the suite against the local PayFlow build on 2026-07-05.
Each entry cites the business rule (docs/business-rules.md) the observed behavior
contradicts. Tests stay red on purpose until the product is fixed.

| # | Area | Observed behavior | Rule violated | Failing tests |
|---|---|---|---|---|
| 1 | Quotes / currencies | GBP→BTC, USD→BTC, GBP→ETH, USD→ETH rejected (422) | all sell EUR/GBP/USD × buy USDC/BTC/ETH pairs are valid | `test_quote_accepts_all_documented_currency_pairs` |
| 2 | Quotes / currencies | USDC→EUR (sides swapped) accepted (201) | sell side is fiat, buy side is crypto | `test_quote_rejects_undocumented_currency_pairs` |
| 3 | Quotes / validation | amount 0 and −50 accepted (201) | amounts must be positive | `test_quote_rejects_non_positive_amount` |
| 4 | Quotes / validation | 50,000.01 and 75,000 accepted (201) | single-payment maximum is 50,000 | `test_quote_rejects_amounts_above_limit` |
| 5 | Quotes / validation | 100.001 accepted (201) | at most 2 decimal places | `test_quote_rejects_more_than_two_decimal_places` |
| 6 | Quote expiry | payment created (201) from a quote older than 120s | expired quote must not be usable | `test_expired_quote_cannot_be_used_for_payment` |
| 7 | KYC gating | customer with status `'Verified'` (capitalized) gets 403 | KYC-approved customers can pay; looks like a case-sensitive status check | `test_payment_gated_by_customer_kyc_status` |
| 8 | Pagination | `limit=N` returns N−1 items; `limit=1` returns 0; paging with `limit=3` drops 2 of 7 records | collection stable and complete across pages | 3 tests in `test_pagination.py` |
| 9 | Web console | no error surfaced when requesting a quote for 50,000.01 | amount limit (as #4), observable in UI | `test_amount_above_limit_surfaces_an_error` |

Suite status on this build: **48 tests, 13 failed / 35 passed** — all 13 triaged as
candidate product bugs; no open test defects (one test defect found during authoring —
timestamp type in the expiry test — was fixed).
