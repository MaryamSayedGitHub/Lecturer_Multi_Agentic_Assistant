from graph_nodes.utils import format_optional
from llm.llm_provider import get_llm
from prompts import RESEARCH_PROMPT
from schemas import OutlineOutput


def research_agent(state) -> dict:
    """Reads: brief.   Writes: outline.

    First version: no web search yet. Tavily comes in Phase 6 (MCP).
    """
    brief = state["brief"]

    chain = RESEARCH_PROMPT | get_llm(temperature=0.3).with_structured_output(OutlineOutput)

    result = chain.invoke({
        "topic": brief["topic"],
        "level": brief["student_level"],
        "duration": brief["duration_minutes"],
        "objectives": format_optional(brief.get("learning_objectives")),
        "search_results": "(web search is not connected yet, use well-established knowledge)",
    })

    return {"outline": result.sections}


if __name__ == "__main__":
    fake_state = {
        "brief": {
            "topic": "Python decorators",
            "student_level": "intermediate",
            "duration_minutes": 60,
            "learning_objectives": ["Students can write their own decorators."],
        },
    }
    out = research_agent(fake_state)

    assert list(out.keys()) == ["outline"]
    assert 3 <= len(out["outline"]) <= 10, f"got {len(out['outline'])} sections"
    for i, s in enumerate(out["outline"], 1):
        print(f"{i}. {s}")
    print("research_agent: OK")