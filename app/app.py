"""Creates the FastAPI app: opens memory once, builds the graph once, mounts API + UI."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config.settings import UI_DIR, setup_logging
from config.tracing import log_tracing_status
from db.checkpointer import open_memory
from graph import build_graph
from GraphController import GraphController
from llm.llm_provider import choose_provider
from routes.session_routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    log_tracing_status()
    choose_provider()  # fail at startup, with a clear message, if no LLM is configured
    with open_memory() as (checkpointer, store):
        app.state.controller = GraphController(build_graph(checkpointer, store))
        yield  # the app serves requests here; the database pool closes afterwards


def create_app() -> FastAPI:
    app = FastAPI(title="Lecturer Agentic Assistant", lifespan=lifespan)
    app.include_router(router)
    # Mounted last, so /api/... is matched first and everything else is the UI.
    app.mount("/", StaticFiles(directory=UI_DIR, html=True), name="ui")
    return app


app = create_app()
