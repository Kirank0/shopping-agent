"""A scripted stand-in for the Groq chat model, so agent tests are fast, free and deterministic."""

from itertools import count

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

_ids = count(1)


class ScriptedChatModel(GenericFakeChatModel):
    """Returns the given AIMessages in order, one per model call.

    create_agent() calls bind_tools(); the fake ignores the tools and returns itself,
    so the scripted tool calls are executed by the real agent loop and real tools.
    """

    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        return self


def tool_call(name: str, **args) -> AIMessage:
    """An AI turn that asks the agent to run one tool."""
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": f"call_{next(_ids)}"}])


def answer(text: str) -> AIMessage:
    """A final AI turn with plain text."""
    return AIMessage(content=text)


def scripted_model(*messages: AIMessage) -> ScriptedChatModel:
    return ScriptedChatModel(messages=iter(messages))


def install_fake_llm(monkeypatch, *messages: AIMessage) -> ScriptedChatModel:
    """Make agent.build_agent() use a scripted model instead of ChatGroq."""
    import agent

    model = scripted_model(*messages)
    monkeypatch.setattr(agent, "ChatGroq", lambda **kwargs: model)
    return model
