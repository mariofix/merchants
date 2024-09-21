from typing import Any

import rich
from fastapi import APIRouter, Body, Request

# from merchants.config import settings
# from merchants.FastapiAdmin import admin
# from merchants.version import __version__ as __merchants_version__

fastapi_route = APIRouter()

# app = FastAPI(
#     title=settings.PROJECT_NAME,
#     version=__merchants_version__,
#     description="A unified payment processing toolkit for Starlette/FastAPI applications",
#     debug=settings.DEBUG,
# )

default_body = Body(None)


@fastapi_route.post(
    "/update-payment/{integration}",
    name="update_payment",
    description="This route processes the status updates from the integrations.",
)
async def update_payment(
    integration: str,
    request: Request,
    body_payload: Any = default_body,
):
    rich.print(f"{body_payload = }")
    rich.print(f"{integration = }")
    rich.print(f"{request.headers = }")
    rich.print(f"{request.query_params = }")
    body = await request.body()
    rich.print(f"{body = }")
    return {"message": "Hello World"}


# app.include_router(app_route, prefix=settings.MERCHANTS_API_ROUTER_PREFIX)
# admin.debug = app.debug
# admin.mount_to(app)


# url_list = [{"path": route.path, "name": route.name} for route in app.routes]
# rich.print(url_list)
