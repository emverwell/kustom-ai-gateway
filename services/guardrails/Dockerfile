# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.12.10@sha256:2bb3ebca0a796a155094a27773d290c4b074572e6107f171d88d086682fd2500 AS uv

# Builder: needs a package toolchain (uv, pip's build backends) that the
# distroless final stage deliberately doesn't have.
FROM python:3.11.16-slim@sha256:9534e5a8e315485d4061ed659af0fd78a284c015f9b73661b41d6bab25604534 AS builder
COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /app

# Dependencies first for layer caching — only re-resolves when these change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Model fetch: pinned by commit SHA inside the script itself, downloaded
# here (build time, network available) so the final image never needs to —
# it only ever reads what's already on disk.
COPY scripts/ scripts/
RUN python scripts/fetch_model.py

COPY app/ app/
COPY config/ config/

# Final: distroless — no shell, no package manager, nothing to exploit
# beyond the interpreter and what we explicitly copied in. Runs as its
# built-in non-root user (65532) by default.
FROM gcr.io/distroless/python3-debian12:nonroot@sha256:7d1042ce588ab97019fe95c24ffca7bc5a82ccdac572511d5e09bda4435c89c5

WORKDIR /app
COPY --from=builder /app/.venv/lib/python3.11/site-packages /app/site-packages
COPY --from=builder /app/app app/
COPY --from=builder /app/config config/
COPY --from=builder /app/.models .models/

ENV PYTHONPATH=/app/site-packages
EXPOSE 8080

CMD ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
