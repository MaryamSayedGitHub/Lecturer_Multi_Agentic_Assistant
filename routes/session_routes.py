"""HTTP endpoints. They validate the request, call GraphController, and translate errors.

The endpoints are normal `def` functions (not async): FastAPI runs them in a worker thread,
which is what we want because a graph run takes many seconds and calls blocking code.
"""

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from config.settings import MAX_REVISIONS, OUTPUT_DIR
from GraphController import (
    GraphController,
    RevisionLimitReached,
    SessionNotFound,
    SessionNotWaiting,
)
from schemas import ApproveRequest, SessionRequest

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


def _controller(request: Request) -> GraphController:
    return request.app.state.controller


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/session")
def create_session(body: SessionRequest, request: Request) -> dict:
    try:
        return _controller(request).start(body.model_dump())
    except Exception as e:
        # The details (which may include provider messages) go to the log, not to the browser.
        log.exception("session failed")
        raise HTTPException(502, f"The session could not be generated ({type(e).__name__}). "
                                 "Check the server log, your API keys and rate limits.") from None


@router.post("/session/approve")
def approve_session(body: ApproveRequest, request: Request) -> dict:
    try:
        return _controller(request).decide(body.session_id, body.decision, body.feedback.strip())
    except SessionNotFound:
        raise HTTPException(404, "Session not found. It may have expired: generate it again.") from None
    except SessionNotWaiting:
        raise HTTPException(409, "This session is not waiting for a decision.") from None
    except RevisionLimitReached:
        raise HTTPException(
            409, f"You already requested changes {MAX_REVISIONS} times. Approve this draft or start a new session."
        ) from None
    except Exception as e:
        log.exception("resume failed")
        raise HTTPException(502, f"The request could not be completed ({type(e).__name__}). "
                                 "Check the server log.") from None


@router.get("/session/{session_id}")
def get_session(session_id: str, request: Request) -> dict:
    try:
        return _controller(request).get_state(session_id)
    except SessionNotFound:
        raise HTTPException(404, "Session not found.") from None


@router.get("/session/{session_id}/files/{name}")
def download_file(session_id: str, name: str, request: Request) -> FileResponse:
    try:
        folder, files = _controller(request).output_folder(session_id)
    except SessionNotFound:
        raise HTTPException(404, "Session not found.") from None
    # Only names the graph itself recorded can be downloaded: no path tricks are possible.
    if not folder or name not in files:
        raise HTTPException(404, "File not found.")
    path = OUTPUT_DIR / folder / name
    if not path.is_file():
        raise HTTPException(404, "File not found.")
    return FileResponse(path, filename=name)
