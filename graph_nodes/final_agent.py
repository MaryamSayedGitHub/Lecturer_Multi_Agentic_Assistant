def final_agent(state) -> dict:
    """TEMPORARY (Phase 5): just copies the draft.

    Later: create the .pptx / code file / quiz file (Phase 6) and save long-term memory (Phase 9).
    """
    return {
        "final_output": {"draft": state["draft"]},
        "messages": ["final_agent: done"],
    }