from datetime import datetime

import pytest

pytestmark = pytest.mark.quotes


def _parse_ts(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

SELL_CURRENCIES = ("EUR", "GBP", "USD")
BUY_CURRENCIES = ("USDC", "BTC", "ETH")
FEE_RATE = 0.015  # 1.5% of the sell amount, per docs/business-rules.md


def _quote(api_client, sell="EUR", buy="USDC", amount=250.00):
    return api_client.post(
        "/api/quotes",
        json={"sell_currency": sell, "buy_currency": buy, "amount": amount},
    )


def test_create_quote_happy_path(api_client):
    response = _quote(api_client)

    assert response.status_code == 201
    quote = response.json()
    assert quote["sell_currency"] == "EUR"
    assert quote["buy_currency"] == "USDC"
    assert quote["amount_in"] == 250.00
    assert quote["fee"] > 0
    assert quote["amount_out"] > 0
    assert quote["id"]
    assert quote["expires_at"] > quote["created_at"]


@pytest.mark.parametrize("amount", [100.00, 250.00, 1333.37, 49999.99])
def test_quote_fee_is_one_point_five_percent(api_client, amount):
    response = _quote(api_client, amount=amount)

    assert response.status_code == 201
    fee = response.json()["fee"]
    expected = round(amount * FEE_RATE, 2)
    assert fee == pytest.approx(expected, abs=0.01), (
        f"fee for {amount} should be 1.5% = {expected}, got {fee}"
    )


def test_quote_expires_120_seconds_after_creation(api_client):
    response = _quote(api_client)

    assert response.status_code == 201
    quote = response.json()
    lifetime = (_parse_ts(quote["expires_at"]) - _parse_ts(quote["created_at"])).total_seconds()
    assert lifetime == pytest.approx(120, abs=2), (
        f"quote lifetime should be 120s, got {lifetime}s"
    )


@pytest.mark.parametrize("sell", SELL_CURRENCIES)
@pytest.mark.parametrize("buy", BUY_CURRENCIES)
def test_quote_accepts_all_documented_currency_pairs(api_client, sell, buy):
    response = _quote(api_client, sell=sell, buy=buy)

    assert response.status_code == 201, f"{sell}->{buy} is a documented pair"


@pytest.mark.parametrize(
    "sell,buy",
    [
        ("USDC", "EUR"),  # sides swapped
        ("BTC", "ETH"),   # crypto on the sell side
        ("EUR", "GBP"),   # fiat on the buy side
        ("JPY", "USDC"),  # undocumented sell currency
        ("EUR", "DOGE"),  # undocumented buy currency
    ],
)
def test_quote_rejects_undocumented_currency_pairs(api_client, sell, buy):
    response = _quote(api_client, sell=sell, buy=buy)

    assert response.status_code == 422, f"{sell}->{buy} is not a documented pair"


@pytest.mark.parametrize("amount", [-50, 0])
def test_quote_rejects_non_positive_amount(api_client, amount):
    response = _quote(api_client, amount=amount)

    assert response.status_code == 422


@pytest.mark.parametrize("amount", [0.01, 49999.99, 50000.00])
def test_quote_accepts_amounts_within_limit(api_client, amount):
    response = _quote(api_client, amount=amount)

    assert response.status_code == 201, f"{amount} is within the 50,000 limit"


@pytest.mark.parametrize("amount", [50000.01, 75000])
def test_quote_rejects_amounts_above_limit(api_client, amount):
    response = _quote(api_client, amount=amount)

    assert response.status_code == 422, f"{amount} exceeds the 50,000 single-payment limit"


def test_quote_rejects_more_than_two_decimal_places(api_client):
    response = _quote(api_client, amount=100.001)

    assert response.status_code == 422
