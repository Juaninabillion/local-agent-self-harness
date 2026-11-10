"""
kernel.py
Fixed core of the self-building agent. Read-only inside the container.
Loads instructions and approved tools from /workspace, keeps memory, runs a chat loop.
"""

import asyncio
import importlib.util
import os
import readline  # noqa: F401  (gives input() arrow keys and history)
import traceback
from pathlib import Path

from openai import AsyncOpenAI
from agents import (
    Agent,
    FunctionTool,
    OpenAIChatCompletionsModel,
    RunHooks,
    Runner,
    SQLiteSession,
    set_tracing_disabled,
)

WORKSPACE = Path("/workspace")
APPROVED = WORKSPACE / "tools" / "approved"
MEMORY_DB = WORKSPACE / "memory" / "session.db"

set_tracing_disabled(True)
client = AsyncOpenAI(base_url=os.environ["OLLAMA_BASE_URL"], api_key="ollama", timeout=600, max_retries=0)
model = OpenAIChatCompletionsModel(model=os.environ["MUSE_MODEL"], openai_client=client)


class ToolLog(RunHooks):
    async def on_tool_start(self, context, agent, tool):
        print(f"[tool] {tool.name}", flush=True)


def load_tools() -> list[FunctionTool]:
    tools = []
    for path in sorted(APPROVED.glob("*.py")):
        try:
            spec = importlib.util.spec_from_file_location(f"tool_{path.stem}", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception:
            print(f"[kernel] failed to load {path.name}:\n{traceback.format_exc()}")
            continue
        found = [obj for obj in vars(module).values() if isinstance(obj, FunctionTool)]
        tools.extend(found)
        print(f"[kernel] loaded {path.name}: {', '.join(t.name for t in found) or 'no tools found'}")
    return tools


def build_agent() -> Agent:
    tools = load_tools()
    installed = ", ".join(t.name for t in tools) or "none"
    instructions = (WORKSPACE / "core" / "prompt.md").read_text()
    instructions += f"\n\n# Current state\n\nTools installed right now: {installed}\n"
    print(f"[kernel] agent ready with {len(tools)} tool(s)")
    return Agent(name="Muse", instructions=instructions, model=model, tools=tools)


async def main():
    MEMORY_DB.parent.mkdir(parents=True, exist_ok=True)
    session = SQLiteSession("muse", str(MEMORY_DB))
    hooks = ToolLog()
    agent = build_agent()
    print("[kernel] commands: /reload (reload prompt and tools), /exit")

    while True:
        try:
            raw = input("\nYou: ")
            # stray bytes from the terminal become lone surrogates that can't be sent as JSON
            user_input = raw.encode("utf-8", "replace").decode("utf-8").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            continue
        if user_input == "/exit":
            break
        if user_input == "/reload":
            agent = build_agent()
            continue
        try:
            result = await Runner.run(agent, user_input, session=session, hooks=hooks, max_turns=20)
            print(f"\nMuse: {result.final_output}")
        except Exception as e:
            print(f"\n[kernel] run failed: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
