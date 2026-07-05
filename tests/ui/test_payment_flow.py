import re

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.ui


def _select_customer_with_status(page, status_substring):
    select = page.get_by_test_id("customer")
    options = select.locator("option")
    labels = options.all_text_contents()
    values = options.evaluate_all("els => els.map(e => e.value)")
    index = next(i for i, label in enumerate(labels) if status_substring.lower() in label.lower())
    select.select_option(value=values[index])


def _request_quote(page, sell="EUR", buy="USDC", amount="250.00"):
    page.get_by_test_id("sell-currency").select_option(sell)
    page.get_by_test_id("buy-currency").select_option(buy)
    page.get_by_test_id("amount").fill(amount)
    page.get_by_test_id("get-quote").click()
    expect(page.get_by_test_id("quote-result")).not_to_have_text("No quote yet.")


def test_verified_customer_can_complete_a_payment(page, base_url):
    page.goto("/")
    _select_customer_with_status(page, "(verified)")
    _request_quote(page)

    create_payment = page.get_by_test_id("create-payment")
    expect(create_payment).to_be_enabled()
    create_payment.click()

    expect(page.get_by_test_id("payment-row").first).to_be_visible()


def test_rejected_customer_sees_an_error_on_payment(page, base_url):
    page.goto("/")
    _select_customer_with_status(page, "(rejected)")
    _request_quote(page)

    page.get_by_test_id("create-payment").click()

    expect(page.get_by_test_id("error")).not_to_be_empty()


def test_quote_result_shows_fee_of_one_point_five_percent(page, base_url):
    page.goto("/")
    _select_customer_with_status(page, "(verified)")
    _request_quote(page, amount="200.00")

    quote_text = page.get_by_test_id("quote-result").inner_text()
    amounts = [float(m) for m in re.findall(r"\d+(?:\.\d+)?", quote_text)]
    expected_fee = 200.00 * 0.015
    assert any(abs(a - expected_fee) < 0.01 for a in amounts), (
        f"quote result should show the 1.5% fee ({expected_fee}), got: {quote_text!r}"
    )


def test_created_payment_shows_a_valid_lifecycle_status(page, base_url):
    page.goto("/")
    _select_customer_with_status(page, "(verified)")
    _request_quote(page)
    page.get_by_test_id("create-payment").click()

    row = page.get_by_test_id("payment-row").first
    expect(row).to_be_visible()
    expect(row).to_contain_text(
        re.compile(r"pending|processing|completed", re.IGNORECASE)
    )


def test_amount_above_limit_surfaces_an_error(page, base_url):
    page.goto("/")
    _select_customer_with_status(page, "(verified)")

    page.get_by_test_id("sell-currency").select_option("EUR")
    page.get_by_test_id("buy-currency").select_option("USDC")
    page.get_by_test_id("amount").fill("50000.01")
    page.get_by_test_id("get-quote").click()

    expect(page.get_by_test_id("error")).not_to_be_empty()
