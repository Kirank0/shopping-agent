"""Helpers for driving the running app in a real browser with Playwright."""

import os

import pytest

BASE_URL = os.environ.get("E2E_BASE_URL", "").rstrip("/")

requires_running_app = pytest.mark.skipif(
    not BASE_URL, reason="set E2E_BASE_URL (e.g. http://localhost:8501) to run browser tests"
)

# Streamlit's own test ids
CHAT_INPUT = '[data-testid="stChatInputTextArea"]'
CHAT_MESSAGE = '[data-testid="stChatMessage"]'
SIDEBAR = '[data-testid="stSidebar"]'

# An LLM call can take a while; give the app time to answer.
ANSWER_TIMEOUT_MS = 90_000


def open_app(page):
    page.goto(BASE_URL)
    page.get_by_role("heading", name="🛒 Shopping Agent").wait_for(timeout=30_000)
    return page


def ask(page, question: str) -> None:
    box = page.locator(CHAT_INPUT)
    box.fill(question)
    box.press("Enter")
