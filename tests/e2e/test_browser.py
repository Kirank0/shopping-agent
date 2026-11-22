"""
Browser end-to-end tests: a real Chromium drives the app as deployed (the Docker container in CI).

The container in these tests runs with a dummy GROQ_API_KEY, so asking a question exercises the
whole stack up to Groq and checks the app reports the failed LLM call gracefully.
Run locally:  E2E_BASE_URL=http://localhost:8501 uv run pytest -m browser
"""

import pytest
from playwright.sync_api import expect

from tests.e2e.browser_helpers import (
    ANSWER_TIMEOUT_MS,
    CHAT_INPUT,
    CHAT_MESSAGE,
    SIDEBAR,
    ask,
    open_app,
    requires_running_app,
)

pytestmark = [pytest.mark.browser, requires_running_app]


def test_page_renders(page):
    open_app(page)

    expect(page.get_by_text("Ask about products, prices, ratings and reviews, or place an order.")).to_be_visible()
    expect(page.locator(CHAT_INPUT)).to_be_visible()
    sidebar = page.locator(SIDEBAR)
    expect(sidebar.get_by_role("button", name="➕ New chat")).to_be_visible()
    expect(sidebar.get_by_role("button", name="Find me organic honey under $20 with ratings above 4.5")).to_be_visible()


def test_question_round_trip_reports_llm_failure_gracefully(page):
    open_app(page)

    ask(page, "What are the best rated coffees?")

    expect(page.locator(CHAT_MESSAGE).first).to_contain_text("What are the best rated coffees?")
    expect(page.get_by_text("Sorry, something went wrong")).to_be_visible(timeout=ANSWER_TIMEOUT_MS)


def test_new_chat_resets_page(page):
    open_app(page)
    ask(page, "hello")
    expect(page.get_by_text("Sorry, something went wrong")).to_be_visible(timeout=ANSWER_TIMEOUT_MS)

    page.locator(SIDEBAR).get_by_role("button", name="➕ New chat").click()

    expect(page.locator(CHAT_MESSAGE)).to_have_count(0)
