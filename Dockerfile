FROM python:3.12-slim

# uv installs the exact versions from uv.lock
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Dependencies first: this layer is rebuilt only when they change.
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

COPY . .

# Do not run as root.
RUN useradd --create-home appuser && mkdir -p outputs && chown -R appuser /app
USER appuser

ENV HOST=0.0.0.0 PORT=8000
EXPOSE 8000
CMD ["uv", "run", "--frozen", "--no-dev", "python", "main.py"]
