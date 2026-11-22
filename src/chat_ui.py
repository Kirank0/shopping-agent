"""Rendering helpers for the Streamlit chat UI (kept separate from app.py so they can be unit-tested)."""

import json

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage


def message_text(message) -> str:
    text = message.text
    return text() if callable(text) else text


def show_markdown(text: str) -> None:
    # Escape "$" so Streamlit doesn't render prices like "$9.99 and $12.99" as LaTeX.
    st.markdown(text.replace("$", "\\$"))


def render_history(messages) -> None:
    tool_calls = []
    for message in messages:
        if isinstance(message, HumanMessage):
            with st.chat_message("user"):
                show_markdown(message_text(message))
            tool_calls = []
        elif isinstance(message, AIMessage):
            if message.tool_calls:
                tool_calls.extend(message.tool_calls)
                continue
            text = message_text(message)
            if not text:
                continue
            with st.chat_message("assistant"):
                if tool_calls:
                    with st.expander(f"🔧 {len(tool_calls)} tool call(s)"):
                        for call in tool_calls:
                            st.code(f"{call['name']}({json.dumps(call['args'])})", language="python")
                show_markdown(text)
            tool_calls = []
