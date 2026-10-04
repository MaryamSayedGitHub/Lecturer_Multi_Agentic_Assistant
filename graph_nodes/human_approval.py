def human_approval(state) -> dict:
    """TEMPORARY (Phase 5): approves automatically.

    Phase 8 replaces this with a real pause using interrupt(), so the lecturer decides.
    """
    return {"approval_status": "approved"}