
from llm.llm_provider import get_llm
from prompts import CODE_PROMPT
from schemas import CodeOutput
from graph_nodes.utils import build_chain, format_optional, format_outline, warn_if_count_differs

def code_agent(state) -> dict:
    """Reads: brief, outline, feedback.   Writes: code_examples.

    First version: the code is NOT executed yet. The run-and-verify loop comes in Phase 6
    (code_runner_server).
    """
    brief = state["brief"]
    num_examples = max(2, min(3, brief["duration_minutes"] // 30))

    chain = build_chain(CODE_PROMPT, CodeOutput, temperature=0.2)
  
    result = chain.invoke({
        "topic": brief["topic"],
        "outline": format_outline(state.get("outline")),
        "level": brief["student_level"],
        "programming_language": brief["programming_language"],
        "num_examples": num_examples,
        "language": brief["language"],
        "feedback": format_optional(state.get("feedback")),
    })

    warn_if_count_differs("code_agent", len(result.examples), num_examples)

    return {"code_examples": [e.model_dump() for e in result.examples]}


if __name__ == "__main__":
    fake_state = {
        "brief": {
            "topic": "Python decorators",
            "student_level": "intermediate",
            "duration_minutes": 60,
            "programming_language": "Python",
            "language": "English",
        },
        "outline": ["Functions are objects", "Closures", "Writing a decorator"],
        "feedback": "",
    }
    out = code_agent(fake_state)

    assert list(out.keys()) == ["code_examples"]
    assert len(out["code_examples"]) > 0
    for e in out["code_examples"]:
        assert e["code"].strip() and e["explanation"].strip()
        print("-", e["title"])
    print("code_agent: OK")