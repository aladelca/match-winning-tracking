"""FastAPI application entrypoint for the mock predictions service."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from match_winning_tracking.api.config import ApiSettings, load_settings
from match_winning_tracking.api.routes import health


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(
        title="Match Winning Tracking API",
        description="Mock predictions API for Liga 1 Peru match outcomes.",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    return app


app = create_app()


def run() -> None:
    import uvicorn

    settings = load_settings()
    uvicorn.run(
        "match_winning_tracking.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
