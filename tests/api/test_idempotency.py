import pytest

pytestmark = pytest.mark.idempotency


def _payment_body(api_client, **extra):
    customers = api_client.get("/api/customers").json()
    verified = next(c for c in customers if c["kyc_status"].strip().lower() == "verified")
    quote = api_client.post(
        "/api/quotes",
        json={"sell_currency": "EUR", "buy_currency": "USDC", "amount": 100.00},
    ).json()
    return {"quote_id": quote["id"], "customer_id": verified["id"], **extra}


def _total_payments(api_client):
    return api_client.get("/api/payments", params={"limit": 1, "offset": 0}).json()["total"]


def test_same_idempotency_key_returns_original_payment(api_client):
    body = _payment_body(api_client, idempotency_key="idem-key-1")

    first = api_client.post("/api/payments", json=body)
    second = api_client.post("/api/payments", json=body)

    assert first.status_code == 201
    assert second.status_code in (200, 201)
    assert second.json()["id"] == first.json()["id"], (
        "retried request with the same idempotency_key must return the original payment"
    )
    assert _total_payments(api_client) == 1, "retry must not create a duplicate payment"


def test_different_idempotency_keys_create_distinct_payments(api_client):
    first = api_client.post(
        "/api/payments", json=_payment_body(api_client, idempotency_key="idem-key-a")
    )
    second = api_client.post(
        "/api/payments", json=_payment_body(api_client, idempotency_key="idem-key-b")
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert _total_payments(api_client) == 2


def test_requests_without_idempotency_key_each_create_a_payment(api_client):
    first = api_client.post("/api/payments", json=_payment_body(api_client))
    second = api_client.post("/api/payments", json=_payment_body(api_client))

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert _total_payments(api_client) == 2
