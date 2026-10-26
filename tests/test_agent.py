import asyncio
from types import SimpleNamespace as NS

import pytest

from agent.agent import MAX_TURNS, run


class FakeSession:
    def __init__(self):
        self.calls = []

    async def list_tools(self):
        return NS(tools=[NS(name="list_unattached_volumes", description="d", inputSchema={"type": "object"})])

    async def call_tool(self, name, args):
        self.calls.append((name, args))
        return NS(content=[NS(type="text", text='[{"id":"vol-1"}]')], isError=False)


def tool_use():
    return NS(stop_reason="tool_use", content=[NS(type="tool_use", id="t1", name="list_unattached_volumes", input={})])


class FakeClient:
    def __init__(self, replies):
        self.replies, self.seen = list(replies), []
        self.messages = NS(create=self.create)

    def create(self, **kw):
        self.seen.append([dict(m) for m in kw["messages"]])
        return self.replies.pop(0)


def test_loop_calls_tool_then_returns_report():
    final = NS(stop_reason="end_turn", content=[NS(type="text", text="REPORT")])
    client, session = FakeClient([tool_use(), final]), FakeSession()
    assert asyncio.run(run(client, session)) == "REPORT"
    assert session.calls == [("list_unattached_volumes", {})]
    result = client.seen[1][-1]["content"][0]  # tool_result echoed back on turn 2
    assert result["tool_use_id"] == "t1" and "vol-1" in result["content"]


def test_loop_is_capped():
    client = FakeClient([tool_use() for _ in range(MAX_TURNS)])
    with pytest.raises(RuntimeError, match="no final answer"):
        asyncio.run(run(client, FakeSession()))
