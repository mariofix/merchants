from typing import Any

import rich
from fastapi import APIRouter, Body, Request

fastapi_route = APIRouter()


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
