import pytest

pytestmark = pytest.mark.pagination


def _create_payment(api_client):
    customers = api_client.get("/api/customers").json()
    verified = next(c for c in customers if c["kyc_status"].strip().lower() == "verified")
    quote = api_client.post(
        "/api/quotes",
        json={"sell_currency": "EUR", "buy_currency": "USDC", "amount": 100.00},
    ).json()

    response = api_client.post(
        "/api/payments",
        json={"quote_id": quote["id"], "customer_id": verified["id"]},
    )
    assert response.status_code == 201
    return response.json()


def test_payment_list_page_matches_requested_limit(api_client):
    for _ in range(5):
        _create_payment(api_client)

    response = api_client.get("/api/payments", params={"limit": 5, "offset": 0})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert len(body["items"]) == 5


def test_payment_list_supports_limit_of_one(api_client):
    _create_payment(api_client)

    response = api_client.get("/api/payments", params={"limit": 1, "offset": 0})

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_paging_through_collection_is_complete_and_duplicate_free(api_client):
    created_ids = {_create_payment(api_client)["id"] for _ in range(7)}

    seen_ids = []
    offset = 0
    while True:
        body = api_client.get("/api/payments", params={"limit": 3, "offset": offset}).json()
        assert body["total"] == 7, "total must be consistent on every page"
        if not body["items"]:
            break
        seen_ids.extend(item["id"] for item in body["items"])
        offset += 3
        assert offset <= 21, "paging did not terminate"

    assert len(seen_ids) == len(set(seen_ids)), "pages must not repeat records"
    assert set(seen_ids) == created_ids, "pages must cover the whole collection"


def test_offset_beyond_total_returns_empty_page(api_client):
    for _ in range(2):
        _create_payment(api_client)

    response = api_client.get("/api/payments", params={"limit": 5, "offset": 10})

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 2
