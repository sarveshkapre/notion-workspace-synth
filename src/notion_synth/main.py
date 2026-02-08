from fastapi import FastAPI

from notion_synth import __version__
from notion_synth.db import connect
from notion_synth.routes import router


def create_app(db_path: str | None = None) -> FastAPI:
    app = FastAPI(title="Notion Workspace Synth", version=__version__)
    app.state.db = connect(db_path)
    app.include_router(router)
    return app


app = create_app()
