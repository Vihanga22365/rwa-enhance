"""Application entry point.

    uvicorn app.main:app --host 0.0.0.0 --port 8000
    python -m app.main
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import router
from app.settings import API_HOST, API_PORT, API_RELOAD, CORS_ORIGINS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    application = FastAPI(title="RWA Explainability API", version=__version__)

    # In the Docker setup the SPA is served from the same origin via nginx, so
    # CORS only matters when the API is called cross-origin (e.g. ng serve on
    # :4200 hitting the API on :8000).
    application.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(router)
    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    # Auto-reload is a development convenience only; keep it OFF in production.
    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=API_RELOAD)
