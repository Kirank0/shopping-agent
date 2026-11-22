"""
Live end-to-end tests against the real Groq model. Opt-in only: they cost API quota and LLM
wording varies, so assertions check facts (products mentioned, rows written), not exact text.

Run locally:  RUN_LIVE=1 uv run pytest -m live
In CI they run on pushes to master, using the GROQ_API_KEY repository secret.
The browser test also needs E2E_BASE_URL pointing at an app started with the real key.
"""

import os

import pytest
import streamlit as st
from playwright.sync_api import expect
from streamlit.testing.v1 import AppTest

from tests.conftest import PROJECT_ROOT, REAL_GROQ_API_KEY
from tests.e2e.browser_helpers import ANSWER_TIMEOUT_MS, CHAT_MESSAGE, ask, open_app, requires_running_app

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.environ.get("RUN_LIVE") != "1", reason="set RUN_LIVE=1 to call the real Groq API"),
    pytest.mark.skipif(not REAL_GROQ_API_KEY, reason="no real GROQ_API_KEY in the environment or .env"),
]


@pytest.fixture
def live_app(monkeypatch, fresh_db):
    monkeypatch.setenv("GROQ_API_KEY", REAL_GROQ_API_KEY)
    st.cache_resource.clear()
    at = AppTest.from_file(str(PROJECT_ROOT / "src" / "app.py"), default_timeout=120)
    at.run()
    yield at
    st.cache_resource.clear()


def last_answer(at: AppTest) -> str:
    assert not at.exception, at.exception
    assert not at.error, at.error[0].value
    assistant = [m for m in at.chat_message if m.name == "assistant"]
    assert assistant, "no assistant reply"
    return " ".join(md.value for md in assistant[-1].markdown)


def test_live_search(live_app):
    live_app.chat_input[0].set_value("Find me organic honey under $20 with ratings above 4.5").run()

    reply = last_answer(live_app)
    # The three matching products in the seed data
    assert sum(name in reply for name in ("Organic Raw Honey", "Organic Buckwheat Honey", "Organic Acacia Honey")) >= 2
    assert "Manuka" not in reply  # $29.99, over budget


def test_live_order(live_app, db_rows):
    live_app.chat_input[0].set_value("Place an order for product ID 5").run()

    last_answer(live_app)
    assert [r["product_id"] for r in db_rows("SELECT product_id FROM orders")] == [5]


@pytest.mark.browser
@requires_running_app
def test_live_browser_answer(page):
    open_app(page)

    ask(page, "What is the cheapest dairy-free milk alternative?")

    expect(page.locator(CHAT_MESSAGE).nth(1)).to_contain_text("Soy Milk", timeout=ANSWER_TIMEOUT_MS)
    expect(page.get_by_text("Sorry, something went wrong")).to_have_count(0)
