from fastapi import FastAPI, Depends, Request
from fastapi.routing import APIRoute
from sqlmodel import Session
from collections.abc import Generator
from typing import Annotated
from merchants.version import __version__ as __merchants_version__

from merchants.config import settings
from merchants.database import engine

from merchants.FastapiAdmin import admin


from debug_toolbar.middleware import DebugToolbarMiddleware
from debug_toolbar.panels.sqlalchemy import SQLAlchemyPanel


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


class SQLModelPanel(SQLAlchemyPanel):
    async def add_engines(self, request: Request):
        self.engines.add(engine)


app = FastAPI(
    title=settings.PROJECT_NAME,
    # generate_unique_id_function=custom_generate_unique_id,
    version=__merchants_version__,
    description="Universal Payment Processing System",
    debug=True,
)
app.add_middleware(
    DebugToolbarMiddleware,
    panels=["merchants.FastapiApp.SQLModelPanel"],
)

admin.mount_to(app)


@app.get("/")
async def root():
    return {"message": "Hello World"}
