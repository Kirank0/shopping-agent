"""Integration tests for the full agent loop: real agent graph, real tools, real DB, scripted LLM."""

import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

import agent
from tests.fakes import answer, install_fake_llm, tool_call


@pytest.fixture(autouse=True)
def _db(fresh_db):
    pass


def run(question: str):
    return agent.build_agent().invoke({"messages": [HumanMessage(question)]}, {"recursion_limit": 20})


def tool_results(result) -> list[ToolMessage]:
    return [m for m in result["messages"] if isinstance(m, ToolMessage)]


def test_search_tool_returns_real_products_to_the_model(monkeypatch):
    install_fake_llm(
        monkeypatch,
        tool_call("search_products", category="honey", max_price=20, min_rating=4.5, organic_only=True),
        answer("Here are three organic honeys."),
    )

    result = run("Find me organic honey under $20 with ratings above 4.5")

    [tool_message] = tool_results(result)
    assert {p["id"] for p in json.loads(tool_message.content)} == {1, 5, 7}
    assert isinstance(result["messages"][-1], AIMessage)
    assert result["messages"][-1].content == "Here are three organic honeys."


def test_multi_step_search_then_reviews(monkeypatch):
    install_fake_llm(
        monkeypatch,
        tool_call("search_products", keyword="manuka"),
        tool_call("get_product_reviews", product_id=3),
        answer("Reviewers love it."),
    )

    result = run("What do reviewers say about the Manuka honey?")

    search, reviews = tool_results(result)
    assert json.loads(search.content)[0]["id"] == 3
    assert len(json.loads(reviews.content)["reviews"]) == 3


def test_place_order_writes_to_database(monkeypatch, db_rows):
    install_fake_llm(monkeypatch, tool_call("place_order", product_id=5), answer("Your order is placed."))

    result = run("Place an order for product ID 5")

    [tool_message] = tool_results(result)
    assert tool_message.content.startswith("Order placed successfully")
    assert [r["product_id"] for r in db_rows("SELECT product_id FROM orders")] == [5]


def test_unknown_product_does_not_create_order(monkeypatch, db_rows):
    install_fake_llm(monkeypatch, tool_call("place_order", product_id=999), answer("That product doesn't exist."))

    result = run("Order product 999")

    assert "Order NOT placed" in tool_results(result)[0].content
    assert db_rows("SELECT * FROM orders") == []


def test_system_prompt_contains_real_categories(monkeypatch):
    model = install_fake_llm(monkeypatch, answer("Hello!"))
    seen = []
    original = type(model)._generate

    def spy(self, messages, *args, **kwargs):
        seen.extend(messages)
        return original(self, messages, *args, **kwargs)

    monkeypatch.setattr(type(model), "_generate", spy)

    run("hi")

    assert "dairy-alt" in seen[0].content
