from fastapi import FastAPI

from notion_synth import __version__
from notion_synth.db import connect
from notion_synth.fault_injection import FaultInjectionMiddleware, fault_injection_enabled
from notion_synth.routes import router


def create_app(db_path: str | None = None) -> FastAPI:
    app = FastAPI(title="Notion Workspace Synth", version=__version__)
    app.state.db = connect(db_path)
    if fault_injection_enabled():
        app.add_middleware(FaultInjectionMiddleware, enabled=True)
    app.include_router(router)
    return app


app = create_app()
