"""Unit tests for the chat rendering helpers, with Streamlit mocked out."""

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

import chat_ui


@pytest.fixture
def st(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(chat_ui, "st", mock)
    return mock


def test_message_text_handles_property_and_method():
    assert chat_ui.message_text(MagicMock(text="plain")) == "plain"
    assert chat_ui.message_text(MagicMock(text=lambda: "called")) == "called"


def test_show_markdown_escapes_dollar_signs(st):
    chat_ui.show_markdown("Honey costs $9.99 and $12.99")
    st.markdown.assert_called_once_with(r"Honey costs \$9.99 and \$12.99")


def test_render_history_shows_user_and_assistant_messages(st):
    chat_ui.render_history([HumanMessage("hello"), AIMessage("Hi! How can I help?")])

    roles = [c.args[0] for c in st.chat_message.call_args_list]
    assert roles == ["user", "assistant"]
    assert [c.args[0] for c in st.markdown.call_args_list] == ["hello", "Hi! How can I help?"]
    st.expander.assert_not_called()


def test_render_history_groups_tool_calls_into_one_expander(st):
    messages = [
        HumanMessage("find honey"),
        AIMessage("", tool_calls=[{"name": "search_products", "args": {"keyword": "honey"}, "id": "1"}]),
        ToolMessage("[...]", tool_call_id="1"),
        AIMessage("", tool_calls=[{"name": "get_product_reviews", "args": {"product_id": 3}, "id": "2"}]),
        ToolMessage("{...}", tool_call_id="2"),
        AIMessage("Here is the honey."),
    ]

    chat_ui.render_history(messages)

    st.expander.assert_called_once_with("🔧 2 tool call(s)")
    codes = [c.args[0] for c in st.code.call_args_list]
    assert codes == ['search_products({"keyword": "honey"})', 'get_product_reviews({"product_id": 3})']


def test_render_history_skips_empty_ai_messages(st):
    chat_ui.render_history([HumanMessage("hi"), AIMessage("")])
    assert [c.args[0] for c in st.chat_message.call_args_list] == ["user"]
