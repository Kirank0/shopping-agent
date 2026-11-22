"""Unit tests for the agent's system prompt and construction."""

import agent
from tests.fakes import answer, install_fake_llm


def test_system_prompt_lists_store_categories(monkeypatch):
    monkeypatch.setattr(agent.products_api, "list_categories", lambda: ["coffee", "honey"])

    prompt = agent._system_prompt()

    assert "coffee, honey" in prompt
    assert "Never invent products" in prompt


def test_build_agent_uses_configured_model(monkeypatch):
    monkeypatch.setattr(agent.products_api, "list_categories", lambda: ["honey"])
    captured = {}
    model = install_fake_llm(monkeypatch, answer("hi"))
    monkeypatch.setattr(agent, "ChatGroq", lambda **kwargs: captured.update(kwargs) or model)

    agent.build_agent()

    assert captured["model"] == agent.MODEL_NAME
    assert captured["temperature"] == 0
