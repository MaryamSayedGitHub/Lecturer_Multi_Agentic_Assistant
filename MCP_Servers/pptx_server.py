"""
Custom MCP server with ONE tool: create_presentation(...).

final_agent uses it to turn the approved slides into a .pptx file.

Safety: the tool only writes inside the project's outputs/ folder. A path that points
anywhere else is rejected, so a model can never make it overwrite other files.

Run the server by itself (it waits for an MCP client on stdin/stdout):
    uv run python MCP_Servers/pptx_server.py
"""

import json
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))  # the server runs as a script: make the project importable

from MCP_Servers.pptx_builder import build_presentation  # noqa: E402

OUTPUT_DIR = (BASE_DIR / "outputs").resolve()

mcp = FastMCP("pptx")


@mcp.tool()
def create_presentation(relative_path: str, deck: dict) -> str:
    """Create a PowerPoint file inside outputs/.

    relative_path: e.g. "session-123/python-decorators.pptx" (must end with .pptx).
    deck: {"title", "course_name", "lecturer", "slides": [...], "code_examples": [...], "quiz": [...]}
          (the full shape is documented in pptx_builder.build_presentation).
    Returns a JSON string: {"ok": bool, "path": str, "error": str}.
    """
    target = (OUTPUT_DIR / relative_path).resolve()
    if not target.is_relative_to(OUTPUT_DIR) or target.suffix != ".pptx":
        return json.dumps({"ok": False, "path": "", "error": "path must be a .pptx inside outputs/"})
    try:
        build_presentation(target, deck)
    except Exception as e:
        return json.dumps({"ok": False, "path": "", "error": f"{type(e).__name__}: {e}"})
    return json.dumps({"ok": True, "path": str(target), "error": ""})


if __name__ == "__main__":
    mcp.run()  # stdio transport
