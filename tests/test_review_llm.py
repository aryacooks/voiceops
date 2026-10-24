"""Verify provider protocol conversion without sending an external request."""
from types import SimpleNamespace

from zentro import llm
from zentro.tools_adapter import TOOLS


class OutputItem(SimpleNamespace):
    def model_dump(self, **kwargs):
        return vars(self)


def test_responses_tool_continuation_preserves_reasoning(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "gpt-6.1-sol")
    monkeypatch.setenv("LLM_API_MODE", "auto")
    requests = []
    reasoning = OutputItem(type="reasoning", id="rs_test", summary=[])
    tool = OutputItem(type="function_call", call_id="call_test", name="date_calc",
                      arguments='{"op":"today"}')

    def create(**kwargs):
        requests.append(kwargs)
        return SimpleNamespace(output=[reasoning, tool], output_text="")

    monkeypatch.setattr(llm, "client", lambda: SimpleNamespace(responses=SimpleNamespace(create=create)))
    messages = [{"role": "user", "content": "What is today's reference date?"}]
    reply = llm.complete(messages, tools=TOOLS)
    messages += [reply.model_dump(exclude_none=True),
                 {"role": "tool", "tool_call_id": "call_test", "content": '{"date":"2026-10-20"}'}]
    llm.complete(messages, tools=TOOLS)
    continuation = requests[-1]["input"]
    assert {"type": "reasoning", "id": "rs_test", "summary": []} in continuation
    assert any(item.get("type") == "function_call_output" and item["call_id"] == "call_test"
               for item in continuation)
    assert "temperature" not in requests[-1]
    assert all(tool["strict"] is False for tool in requests[-1]["tools"])
