"""Application entrypoint:   uv run python main.py   then open http://localhost:8000"""

import uvicorn

from config.settings import HOST, PORT

if __name__ == "__main__":
    uvicorn.run("app.app:app", host=HOST, port=PORT)
