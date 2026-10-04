"""Save the graph diagram as a PNG:   uv run python draw_graph.py"""
from pathlib import Path

from graph import build_graph

if __name__ == "__main__":
    graph = build_graph()  # no LLM call happens here, so no API key is needed

    out = Path("docs")
    out.mkdir(exist_ok=True)

    # The Mermaid text is always saved: it works even when the PNG download fails.
    (out / "graph.mmd").write_text(graph.get_graph().draw_mermaid(), encoding="utf-8")
    print("saved docs/graph.mmd")

    try:
        (out / "graph.png").write_bytes(graph.get_graph().draw_mermaid_png())
        print("saved docs/graph.png")
    except Exception as e:
        print(f"PNG failed ({type(e).__name__}: {e})")
        print("Open docs/graph.mmd, paste it at https://mermaid.live and export PNG from there.")