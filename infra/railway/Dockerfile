# NoteLens key-free mock demo: Next.js web + three Python mock services in one container.
FROM node:24-bookworm-slim

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/

ENV NEXT_TELEMETRY_DISABLED=1 \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=0 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY . .

RUN uv python install 3.13 \
 && for service in services/rag services/classifier services/extraction; do \
      uv sync --locked --directory "$service" --python 3.13 --no-dev || exit 1; \
    done

RUN npm ci --no-audit --no-fund && npm run build

ENV NODE_ENV=production
RUN chmod +x infra/railway/start.sh
EXPOSE 3000
CMD ["infra/railway/start.sh"]
