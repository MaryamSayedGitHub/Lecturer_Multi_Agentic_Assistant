"""Phase 5 checkpoint: run the whole graph from a script.   uv run python run_graph.py"""
from dotenv import load_dotenv

load_dotenv()

from graph import build_graph  # noqa: E402

if __name__ == "__main__":
    graph = build_graph()

    # Print the diagram (paste it at https://mermaid.live to see it).
    print(graph.get_graph().draw_mermaid())

    initial_state = {
        "brief": {
            "session_id": "test-1",
            "lecturer_id": "dr-sara",
            "topic": "Python decorators",
            "course_name": "Advanced Python",
            "student_level": "intermediate",
            "duration_minutes": 60,
            "language": "English",
            "programming_language": "Python",
            "needs": ["slides", "code", "quiz"],
            "num_quiz_questions": 3,
            "learning_objectives": ["Students can write their own decorators."],
            "notes": "Keep slides short.",
        },
        "memory_context": [],
        "feedback": "",
        "revision_count": 0,
        "approval_status": "pending",
        "messages": [],
    }

    config = {"configurable": {"thread_id": "test-1"}}

    # stream_mode="updates" shows which node ran and what it wrote.
    for update in graph.stream(initial_state, config, stream_mode="updates"):
        for node, changes in update.items():
            print(f"[{node}] wrote: {list(changes.keys())}")

    final = graph.get_state(config).values
    print("\nselected_agents:", final["selected_agents"])
    print("outline:", final["outline"])
    print("slides:", len(final["slides"]), "| code:", len(final["code_examples"]), "| quiz:", len(final["quiz"]))