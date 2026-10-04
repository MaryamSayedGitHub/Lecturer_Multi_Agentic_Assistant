"""
Phase 6 checkpoint (part 1): test the code_runner MCP server on its own.

    uv run python test_code_runner.py

Step A calls the function directly (fast, easy to debug).
Step B starts the server as a separate process and calls it through the real MCP protocol,
which is exactly what the code_agent will do later.
"""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from MCP_Servers.code_runner_server import run_python

CASES = {
    "prints":        ("print('hello')",                                   lambda r: r["ok"] and "hello" in r["stdout"]),
    "syntax error":  ("def f(:\n    pass",                                lambda r: not r["ok"] and "SyntaxError" in r["stderr"]),
    "runtime error": ("print(1/0)",                                       lambda r: not r["ok"] and "ZeroDivisionError" in r["stderr"]),
    "infinite loop": ("while True:\n    pass",                           lambda r: r["timed_out"]),
    "no secrets":    ("import os\nprint(os.environ.get('GROQ_API_KEY'))", lambda r: r["ok"] and "None" in r["stdout"]),
    "input() fails fast": ("input('name? ')",                             lambda r: not r["ok"] and "EOFError" in r["stderr"]),
    "long output":   ("print('x' * 100000)",                              lambda r: r["ok"] and "truncated" in r["stdout"]),
}


def check(label: str, result: dict, test) -> None:
    status = "OK  " if test(result) else "FAIL"
    print(f"  [{status}] {label}")
    if status == "FAIL":
        print("         got:", {k: (v[:80] if isinstance(v, str) else v) for k, v in result.items()})


def step_a_direct() -> None:
    print("== A) direct call ==")
    os.environ["GROQ_API_KEY"] = "secret-test-key"  # must NOT reach the child process
    for label, (code, test) in CASES.items():
        check(label, json.loads(run_python(code)), test)


async def step_b_mcp() -> None:
    print("== B) through MCP (stdio) ==")
    params = StdioServerParameters(command=sys.executable, args=["MCP_Servers/code_runner_server.py"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("  tools:", [t.name for t in tools.tools])

            for label, (code, test) in CASES.items():
                reply = await session.call_tool("run_python", {"code": code})
                check(label, json.loads(reply.content[0].text), test)

if __name__ == "__main__":
    step_a_direct()
    asyncio.run(step_b_mcp())