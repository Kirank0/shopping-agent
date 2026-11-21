"""
Streamlit chat UI for the shopping agent.

Run from the project root:  uv run streamlit run src/app.py
"""

import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Load .env before importing modules that read environment variables at import time.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from langchain_core.messages import AIMessage, HumanMessage  # noqa: E402

from agent import build_agent  # noqa: E402
from setup_db import DB_PATH, create_database  # noqa: E402

EXAMPLES = [
    "Find me organic honey under $20 with ratings above 4.5",
    "What do reviewers say about the Manuka honey?",
    "What is the cheapest dairy-free milk alternative?",
    "What are the best rated coffees?",
    "Place an order for product ID 5",
    "Order the Organic Almonds",
]

st.set_page_config(page_title="Shopping Agent", page_icon="🛒", layout="centered")


@st.cache_resource
def get_agent():
    if not os.path.exists(DB_PATH):
        create_database()
    return build_agent()


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


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    if st.button("➕ New chat", type="primary", width="stretch"):
        st.session_state.messages = []
        st.rerun()
    st.subheader("Try asking")
    clicked_example = None
    for example in EXAMPLES:
        if st.button(example, key=f"example-{example}", width="stretch"):
            clicked_example = example

st.title("🛒 Shopping Agent")
st.caption("Ask about products, prices, ratings and reviews, or place an order.")

if not os.getenv("GROQ_API_KEY"):
    st.error("GROQ_API_KEY is not set. Copy `.env.example` to `.env` and add your Groq API key.")
    st.stop()

render_history(st.session_state.messages)

prompt = st.chat_input("Ask about products or place an order...") or clicked_example
if prompt:
    with st.chat_message("user"):
        show_markdown(prompt)
    history = st.session_state.messages + [HumanMessage(prompt)]
    try:
        with st.spinner("Thinking..."):
            result = get_agent().invoke({"messages": history}, {"recursion_limit": 20})
    except Exception as error:
        with st.chat_message("assistant"):
            st.error(f"Sorry, something went wrong: {error}")
    else:
        st.session_state.messages = result["messages"]
        st.rerun()
