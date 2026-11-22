"""
End-to-end tests of the Streamlit app with Streamlit's headless AppTest runner.

The real app.py runs top to bottom (UI, agent, tools, SQLite); only the LLM is scripted.
"""

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import agent
from tests.conftest import PROJECT_ROOT
from tests.fakes import answer, install_fake_llm, tool_call

APP_PATH = str(PROJECT_ROOT / "src" / "app.py")
EXAMPLE = "Place an order for product ID 5"


@pytest.fixture(autouse=True)
def _clean_app_state(fresh_db):
    st.cache_resource.clear()  # the app caches the agent; each test gets a new one
    yield
    st.cache_resource.clear()


def start_app() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    return at


def chat(at: AppTest) -> list[tuple[str, str]]:
    """The visible conversation as (role, text) pairs."""
    return [(m.name, " ".join(md.value for md in m.markdown)) for m in at.chat_message]


def test_page_loads(monkeypatch):
    at = start_app()

    assert at.title[0].value == "🛒 Shopping Agent"
    assert "place an order" in at.caption[0].value
    labels = [b.label for b in at.sidebar.button]
    assert labels[0] == "➕ New chat"
    assert len(labels) == 7  # New chat + six example questions
    assert EXAMPLE in labels
    assert at.chat_input
    assert not at.error


def test_missing_api_key_shows_error(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "")  # load_dotenv won't override a set variable

    at = start_app()

    assert "GROQ_API_KEY is not set" in at.error[0].value
    assert not at.chat_input


def test_chat_question_gets_answer_with_tool_calls(monkeypatch):
    install_fake_llm(
        monkeypatch,
        tool_call("search_products", keyword="coffee", sort_by="rating"),
        answer("The best rated coffee is Organic Ethiopian Coffee at $16.99."),
    )
    at = start_app()

    at.chat_input[0].set_value("What are the best rated coffees?").run()

    assert not at.exception, at.exception
    assert chat(at) == [
        ("user", "What are the best rated coffees?"),
        ("assistant", r"The best rated coffee is Organic Ethiopian Coffee at \$16.99."),
    ]
    assert at.expander[0].label == "🔧 1 tool call(s)"
    assert 'search_products({"keyword": "coffee", "sort_by": "rating"})' in at.code[0].value


def test_example_button_places_order(monkeypatch, db_rows):
    install_fake_llm(monkeypatch, tool_call("place_order", product_id=5), answer("Order #1 placed."))
    at = start_app()

    at.button(key=f"example-{EXAMPLE}").click().run()

    assert not at.exception, at.exception
    assert chat(at) == [("user", EXAMPLE), ("assistant", "Order #1 placed.")]
    assert [r["product_id"] for r in db_rows("SELECT product_id FROM orders")] == [5]


def test_conversation_keeps_history_across_turns(monkeypatch):
    install_fake_llm(monkeypatch, answer("Hello! Ask me about products."), answer("We sell honey and more."))
    at = start_app()

    at.chat_input[0].set_value("hi").run()
    at.chat_input[0].set_value("what do you sell?").run()

    assert [role for role, _ in chat(at)] == ["user", "assistant", "user", "assistant"]
    assert chat(at)[-1] == ("assistant", "We sell honey and more.")


def test_new_chat_clears_history(monkeypatch):
    install_fake_llm(monkeypatch, answer("Hello!"))
    at = start_app()
    at.chat_input[0].set_value("hi").run()
    assert chat(at)

    at.sidebar.button[0].click().run()

    assert chat(at) == []
    assert at.session_state.messages == []


def test_agent_failure_is_shown_gracefully(monkeypatch):
    class BrokenAgent:
        def invoke(self, *args, **kwargs):
            raise RuntimeError("Groq is unavailable")

    monkeypatch.setattr(agent, "build_agent", lambda: BrokenAgent())
    at = start_app()

    at.chat_input[0].set_value("hi").run()

    assert not at.exception
    assert "Sorry, something went wrong: Groq is unavailable" in at.error[0].value
    assert at.session_state.messages == []  # failed turn is not saved
