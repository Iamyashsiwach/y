"""FinOps agent loop: Claude calls the read-only AWS MCP tools, then reports ranked savings.
Run: ANTHROPIC_API_KEY=... python -m agent.agent
"""
import asyncio
import os
import sys

import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = os.environ.get("FINOPS_MODEL", "claude-opus-5-5")
MAX_TURNS = 10  # hard cap on tool-use rounds so a confused run can't loop (and bill) forever

SYSTEM = """You are a FinOps agent for a personal AWS account. Use the tools to find wasted spend, then write a report.
Rules: only report what the tools returned; never invent resource ids or costs.
Report: a markdown table ranked by est_monthly_usd (highest first) with resource id, why it is waste, and a proposed
Terraform change (resource to remove or resize). End with the total estimated monthly savings.
You are read-only: propose changes, never claim to have applied them."""


async def run(client, session, model: str = MODEL) -> str:
    listed = await session.list_tools()
    tools = [{"name": t.name, "description": t.description or "", "input_schema": t.inputSchema} for t in listed.tools]
    messages = [{"role": "user", "content": "Audit the account for waste and write the ranked report."}]

    for _ in range(MAX_TURNS):
        resp = client.messages.create(model=model, max_tokens=16000, system=SYSTEM, tools=tools, messages=messages)
        if resp.stop_reason == "refusal":
            raise RuntimeError(f"model refused: {resp.stop_details}")
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text")

        messages.append({"role": "assistant", "content": resp.content})
        results = []  # all results go back in ONE user message (parallel tool use)
        for b in resp.content:
            if b.type != "tool_use":
                continue
            out = await session.call_tool(b.name, b.input)
            results.append({
                "type": "tool_result",
                "tool_use_id": b.id,
                "content": "".join(c.text for c in out.content if c.type == "text"),
                "is_error": bool(out.isError),
            })
        messages.append({"role": "user", "content": results})
    raise RuntimeError(f"no final answer after {MAX_TURNS} turns")


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"])
    async with stdio_client(params) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        print(await run(anthropic.Anthropic(), session))


if __name__ == "__main__":
    asyncio.run(main())
