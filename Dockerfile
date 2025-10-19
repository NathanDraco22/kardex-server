FROM python:3.12.12-slim-bookworm

RUN mkdir -p /home/server

WORKDIR /home/server

RUN pip install uv

COPY pyproject.toml .
COPY uv.lock .

RUN uv sync --frozen --no-dev

COPY . .

WORKDIR /home/server/app

CMD . ../.venv/bin/activate && fastapi run --host 0.0.0.0