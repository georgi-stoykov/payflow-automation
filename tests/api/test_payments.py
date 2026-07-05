import time

import pytest

pytestmark = pytest.mark.payments

TERMINAL_STATUSES = ("completed", "failed", "reversed")


def _quote(api_client, sell="EUR", buy="USDC", amount=250.00):
    response = api_client.post(
        "/api/quotes",
        json={"sell_currency": sell, "buy_currency": buy, "amount": amount},
    )
    assert response.status_code == 201
    return response.json()


def _verified_customer(api_client):
    customers = api_client.get("/api/customers").json()
    return next(c for c in customers if c["kyc_status"].strip().lower() == "verified")


def _create_payment(api_client, **overrides):
    body = {
        "quote_id": overrides.pop("quote_id", None) or _quote(api_client)["id"],
        "customer_id": overrides.pop("customer_id", None) or _verified_customer(api_client)["id"],
    }
    body.update(overrides)
    return api_client.post("/api/payments", json=body)


def test_create_payment_happy_path(api_client):
    verified = _verified_customer(api_client)
    quote = _quote(api_client)

    response = api_client.post(
        "/api/payments",
        json={"quote_id": quote["id"], "customer_id": verified["id"]},
    )

    assert response.status_code == 201
    payment = response.json()
    assert payment["quote_id"] == quote["id"]
    assert payment["customer_id"] == verified["id"]
    assert payment["status"] in ("pending", "processing", "completed")


def test_get_payment_by_id_returns_created_payment(api_client):
    created = _create_payment(api_client).json()

    response = api_client.get(f"/api/payments/{created['id']}")

    assert response.status_code == 200
    fetched = response.json()
    assert fetched["id"] == created["id"]
    assert fetched["quote_id"] == created["quote_id"]
    assert fetched["customer_id"] == created["customer_id"]


def test_payment_rejects_unknown_quote_id(api_client):
    verified = _verified_customer(api_client)

    response = api_client.post(
        "/api/payments",
        json={"quote_id": "q_does_not_exist", "customer_id": verified["id"]},
    )

    assert response.status_code in (404, 422)


def test_payment_rejects_unknown_customer_id(api_client):
    quote = _quote(api_client)

    response = api_client.post(
        "/api/payments",
        json={"quote_id": quote["id"], "customer_id": "cus_does_not_exist"},
    )

    assert response.status_code in (404, 422)


@pytest.mark.kyc
def test_payment_gated_by_customer_kyc_status(api_client):
    customers = api_client.get("/api/customers").json()

    for customer in customers:
        quote = _quote(api_client)
        response = api_client.post(
            "/api/payments",
            json={"quote_id": quote["id"], "customer_id": customer["id"]},
        )

        if customer["kyc_status"].strip().lower() == "verified":
            assert response.status_code == 201, (
                f"customer {customer['id']} ({customer['kyc_status']!r}) should be allowed to pay"
            )
        else:
            assert response.status_code == 403, (
                f"customer {customer['id']} ({customer['kyc_status']!r}) should be blocked from paying"
            )


@pytest.mark.slow
def test_expired_quote_cannot_be_used_for_payment(api_client):
    quote = _quote(api_client)
    verified = _verified_customer(api_client)

    time.sleep(125)  # quotes expire 120s after creation

    response = api_client.post(
        "/api/payments",
        json={"quote_id": quote["id"], "customer_id": verified["id"]},
    )

    assert response.status_code in (409, 410, 422), (
        f"expired quote must be rejected, got {response.status_code}"
    )


@pytest.mark.slow
def test_payment_lifecycle_advances_with_age(api_client):
    payment = _create_payment(api_client).json()
    assert payment["status"] == "pending"

    time.sleep(4)  # processing after ~3s
    mid = api_client.get(f"/api/payments/{payment['id']}").json()
    assert mid["status"] in ("processing", "completed")

    time.sleep(5)  # completed after ~8s total
    final = api_client.get(f"/api/payments/{payment['id']}").json()
    assert final["status"] == "completed"


@pytest.mark.parametrize("status", TERMINAL_STATUSES)
def test_webhook_forces_terminal_status(api_client, status):
    payment = _create_payment(api_client).json()

    response = api_client.post(f"/api/webhooks/simulate/{payment['id']}", params={"status": status})

    assert response.status_code == 200
    assert api_client.get(f"/api/payments/{payment['id']}").json()["status"] == status


@pytest.mark.slow
def test_terminal_status_is_not_overridden_by_age(api_client):
    payment = _create_payment(api_client).json()
    api_client.post(f"/api/webhooks/simulate/{payment['id']}", params={"status": "failed"})

    time.sleep(9)  # past the point age would normally complete the payment

    assert api_client.get(f"/api/payments/{payment['id']}").json()["status"] == "failed"
