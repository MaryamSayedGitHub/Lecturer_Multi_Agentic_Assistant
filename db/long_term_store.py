"""LONG-TERM memory: what we keep about a lecturer ACROSS sessions (LangGraph Store).

Namespaces:
  ("lecturer", <id>, "preferences")  key "defaults"     -> language, level, code language
  ("lecturer", <id>, "feedback")     key <session_id>   -> change requests from that session
  ("lecturer", <id>, "sessions")     key <session_id>   -> topic + outline of a finished session

Everything here is plain data written by code. No LLM decides what is remembered,
so the memory can always be traced back to something the lecturer actually did.

The store itself is opened in db/checkpointer.py (same Postgres pool) and given to the graph
with compile(store=...). Nodes get it with current_store().
"""

import logging

log = logging.getLogger(__name__)

MAX_FEEDBACK_ITEMS = 5
MAX_SESSION_ITEMS = 3


def lecturer_key(lecturer_id: str) -> str:
    """'Dr. Sara ' and 'dr. sara' must be the same lecturer."""
    return " ".join(lecturer_id.strip().lower().split())


def current_store():
    """The store of the running graph, or None (e.g. when a node is tested by itself)."""
    try:
        from langgraph.config import get_store

        return get_store()
    except Exception:  # not inside a graph run, or the graph has no store
        return None


def load_memory(store, lecturer_id: str) -> list[str]:
    """Return short sentences for the prompts. Empty list if nothing is known."""
    if store is None or not lecturer_id:
        return []
    base = ("lecturer", lecturer_key(lecturer_id))
    lines: list[str] = []
    try:
        prefs = store.get((*base, "preferences"), "defaults")
        if prefs:
            v = prefs.value
            lines.append(
                f"Usually teaches in {v.get('language')}, code in {v.get('programming_language')}, "
                f"for {v.get('student_level')} students."
            )
        for item in store.search((*base, "feedback"), limit=MAX_FEEDBACK_ITEMS):
            for text in item.value.get("items", []):
                lines.append(f"Earlier change request: {text}")
        for item in store.search((*base, "sessions"), limit=MAX_SESSION_ITEMS):
            v = item.value
            lines.append(f"Previous session: {v.get('topic')} ({', '.join(v.get('outline', [])[:4])})")
    except Exception as e:  # memory is helpful, never required
        log.warning("Could not read long-term memory: %s: %s", type(e).__name__, str(e)[:200])
        return []
    return lines


def save_session(store, brief: dict, outline: list[str], feedback_history: list[str]) -> bool:
    """Called by final_agent after the lecturer approved. Returns True if it was saved."""
    lecturer_id = brief.get("lecturer_id", "")
    if store is None or not lecturer_id:
        return False
    base = ("lecturer", lecturer_key(lecturer_id))
    session_id = brief["session_id"]
    try:
        store.put((*base, "preferences"), "defaults", {
            "language": brief.get("language"),
            "programming_language": brief.get("programming_language"),
            "student_level": brief.get("student_level"),
        })
        store.put((*base, "sessions"), session_id, {
            "topic": brief.get("topic"),
            "course_name": brief.get("course_name"),
            "outline": outline,
        })
        if feedback_history:
            store.put((*base, "feedback"), session_id, {"items": feedback_history})
    except Exception as e:
        log.warning("Could not save long-term memory: %s: %s", type(e).__name__, str(e)[:200])
        return False
    return True
