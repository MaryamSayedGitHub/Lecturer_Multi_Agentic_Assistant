"""Run the whole graph from a script, approving the draft automatically.

    uv run python run_graph.py
"""
from dotenv import load_dotenv

load_dotenv()

from langgraph.types import Command  # noqa: E402

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
        "feedback_history": [],
        "revision_count": 0,
        "approval_status": "pending",
        "messages": [],
    }

    config = {"configurable": {"thread_id": "test-1"}}

    def show(stream):
        # stream_mode="updates" shows which node ran and what it wrote.
        for update in stream:
            for node, changes in update.items():
                keys = list(changes.keys()) if isinstance(changes, dict) else "(paused)"
                print(f"[{node}] wrote: {keys}")

    show(graph.stream(initial_state, config, stream_mode="updates"))

    # The graph is now paused at human_approval. A real lecturer decides in the UI;
    # here we approve so the script also exercises final_agent.
    print("next:", graph.get_state(config).next)
    show(graph.stream(Command(resume={"decision": "approve"}), config, stream_mode="updates"))

    final = graph.get_state(config).values
    print("\nselected_agents:", final["selected_agents"])
    print("outline:", final["outline"])
    print("slides:", len(final["slides"]), "| code:", len(final["code_examples"]), "| quiz:", len(final["quiz"]))
    print("files:", final["final_output"])
