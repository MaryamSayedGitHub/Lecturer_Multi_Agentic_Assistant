"""Central settings: every value comes from .env, never from the code."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)
UI_DIR = BASE_DIR / "ui"

# LLM
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Tools
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Database. Empty = run without Postgres (memory is lost when the app stops).
DATABASE_URL = os.getenv("DATABASE_URL") or None

# Human-in-the-loop: how many times the lecturer may send a draft back.
MAX_REVISIONS = int(os.getenv("MAX_REVISIONS", "3"))

# Server
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def setup_logging() -> None:
    """Call once at startup. Agents log through logging.getLogger(__name__)."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
