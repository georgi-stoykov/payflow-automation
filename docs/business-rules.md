# PayFlow — public contract and business rules

Everything in this document comes from the service's published API documentation
(`/docs`, `/openapi.json`) and the product team's stated business rules. It is the
single source of truth for test assertions.

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | Service health |
| GET | `/api/customers` | Customers with their KYC state |
| POST | `/api/quotes` | `{sell_currency, buy_currency, amount}` → rate, fee, expiry |
| POST | `/api/payments` | `{quote_id, customer_id, idempotency_key?}` |
| GET | `/api/payments/{id}` | Payment by id |
| GET | `/api/payments?limit=&offset=` | Paginated list |
| POST | `/api/webhooks/simulate/{id}?status=` | Test hook: force `completed\|failed\|reversed` |
| POST | `/api/admin/reset` | Test hook: clear all state |

## Business rules

- **Currencies**: sell side EUR/GBP/USD, buy side USDC/BTC/ETH.
- **Quotes**: fee is **1.5%** of the sell amount; a quote **expires 120 seconds**
  after creation and must not be usable for a payment afterwards.
- **Payments**: created from a valid, unexpired quote for a KYC-approved customer.
  Lifecycle is `pending → processing → completed`; a payment advances with age
  (processing after ~3s, completed after ~8s) unless a webhook forces a terminal
  state (`completed`, `failed`, `reversed`).
- **KYC gating**: customers who are not KYC-approved must not be able to create
  payments.
- **Idempotency**: re-sending a payment request with the same `idempotency_key`
  must return the original payment, not create a duplicate.
- **Pagination**: `limit`/`offset` semantics on the payments list; the collection
  must be stable and complete across pages (no dropped or duplicated records).
- **Amount limits**: single-payment maximum is 50,000 in sell currency; amounts
  must be positive with at most 2 decimal places.
