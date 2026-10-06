"""Evaluate the graph on evals/dataset.json.

    uv run python evals/run_eval.py            # local: prints a table, no LangSmith needed
    uv run python evals/run_eval.py --langsmith  # also uploads the experiment to LangSmith

Each brief runs up to the human-approval pause and the DRAFT is checked. The checks are
plain code (no LLM judge), so a failing score always points at something concrete.
This makes real LLM calls: mind your provider's rate limits.
"""

import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.tracing import run_config  # noqa: E402
from graph import build_graph  # noqa: E402

DATASET_NAME = "lecturer-assistant-briefs"


def run_brief(brief: dict) -> dict:
    """The target: brief in, draft out."""
    graph = build_graph()
    session_id = uuid.uuid4().hex
    config = run_config(session_id, brief.get("lecturer_id", ""))
    graph.invoke(
        {
            "brief": {**brief, "session_id": session_id},
            "memory_context": [], "feedback": "", "feedback_history": [],
            "revision_count": 0, "approval_status": "pending", "messages": [],
        },
        config,
    )
    values = graph.get_state(config).values
    return {"draft": values.get("draft", {}), "selected_agents": values.get("selected_agents", [])}


# ---------------------------------------------------------------- evaluators
# Each returns True / False. `inputs` is the brief, `outputs` is what run_brief returned.
def requested_parts_present(inputs: dict, outputs: dict) -> bool:
    draft = outputs["draft"]
    keys = {"slides": "slides", "code": "code_examples", "quiz": "quiz"}
    return bool(draft.get("outline")) and all(draft.get(keys[n]) for n in inputs["needs"])


def slide_count_fits(inputs: dict, outputs: dict) -> bool:
    if "slides" not in inputs["needs"]:
        return True
    expected = max(5, min(8, inputs["duration_minutes"] // 8))  # same formula as slides_agent
    return abs(len(outputs["draft"].get("slides", [])) - expected) <= 1


def quiz_is_valid(inputs: dict, outputs: dict) -> bool:
    if "quiz" not in inputs["needs"]:
        return True
    quiz = outputs["draft"].get("quiz", [])
    return len(quiz) == inputs["num_quiz_questions"] and all(
        len(q["options"]) == 4 and 0 <= q["answer_index"] < 4 for q in quiz
    )


def code_examples_run(inputs: dict, outputs: dict) -> bool:
    if "code" not in inputs["needs"]:
        return True
    examples = outputs["draft"].get("code_examples", [])
    return bool(examples) and all(e.get("verified") is True for e in examples)


EVALUATORS = [requested_parts_present, slide_count_fits, quiz_is_valid, code_examples_run]


def run_local(briefs: list[dict]) -> None:
    totals = {e.__name__: 0 for e in EVALUATORS}
    for brief in briefs:
        try:
            outputs = run_brief(brief)
        except Exception as e:
            print(f"{brief['topic']:25} FAILED TO RUN: {type(e).__name__}: {str(e)[:120]}")
            continue
        scores = {e.__name__: e(brief, outputs) for e in EVALUATORS}
        for name, ok in scores.items():
            totals[name] += ok
        print(f"{brief['topic']:25} " + "  ".join(f"{n}={'PASS' if ok else 'FAIL'}" for n, ok in scores.items()))
    print("\nPassed, out of", len(briefs))
    for name, passed in totals.items():
        print(f"  {name:28} {passed}")


def run_langsmith(briefs: list[dict]) -> None:
    from langsmith import Client

    client = Client()
    if not client.has_dataset(dataset_name=DATASET_NAME):
        dataset = client.create_dataset(DATASET_NAME, description="Sample session briefs")
        client.create_examples(dataset_id=dataset.id, inputs=briefs)
    client.evaluate(
        run_brief,
        data=DATASET_NAME,
        evaluators=EVALUATORS,
        experiment_prefix="lecturer-assistant",
        max_concurrency=1,  # free-tier rate limits
    )
    print("Done. Open your LangSmith project to see the experiment.")


if __name__ == "__main__":
    briefs = json.loads((ROOT / "evals" / "dataset.json").read_text(encoding="utf-8"))
    if "--langsmith" in sys.argv:
        run_langsmith(briefs)
    else:
        run_local(briefs)
