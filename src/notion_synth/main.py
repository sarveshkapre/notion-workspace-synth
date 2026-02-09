import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from notion_synth import __version__
from notion_synth.db import connect
from notion_synth.fault_injection import FaultInjectionMiddleware, fault_injection_enabled
from notion_synth.routes import router

_TRUTHY = {"1", "true", "yes", "on"}


def _cors_origins() -> list[str] | None:
    """
    Optional CORS for local demo UIs.

    Enable by setting NOTION_SYNTH_CORS_ORIGINS to a comma-separated list of origins
    (example: "http://localhost:5173,http://localhost:3000") or "*".
    """

    raw = os.getenv("NOTION_SYNTH_CORS_ORIGINS", "").strip()
    if not raw:
        return None
    if raw == "*":
        return ["*"]
    origins = [part.strip() for part in raw.split(",")]
    origins = [o for o in origins if o]
    return origins or None


def _cors_allow_credentials() -> bool:
    return os.getenv("NOTION_SYNTH_CORS_ALLOW_CREDENTIALS", "").strip().lower() in _TRUTHY


def create_app(db_path: str | None = None) -> FastAPI:
    app = FastAPI(title="Notion Workspace Synth", version=__version__)
    app.state.db = connect(db_path)
    cors_origins = _cors_origins()
    if cors_origins:
        # For browser demo clients: expose paging/metadata headers.
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=_cors_allow_credentials(),
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=[
                "X-Total-Count",
                "X-Limit",
                "X-Offset",
                "X-Has-More",
                "X-Next-Offset",
                "Link",
                "X-Notion-Synth-Delay-Ms",
                "X-Notion-Synth-Fault-Injected",
            ],
        )
    if fault_injection_enabled():
        app.add_middleware(FaultInjectionMiddleware, enabled=True)
    app.include_router(router)
    return app


app = create_app()
