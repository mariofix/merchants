import pytest  # noqa
from fastapi import FastAPI
from fastapi.testclient import TestClient

from merchants.StarletteApp import fastapi_route
from merchants.version import __version__

app = FastAPI()
app.include_router(fastapi_route)
client = TestClient(app)


def test_version():
    assert __version__ == "2024.9.16"


def test_update_payment_success():
    response = client.post(
        "/update-payment/test_integration", json={"key": "value"}, headers={"Custom-Header": "Test"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_update_payment_different_integration():
    response = client.post(
        "/update-payment/another_integration", json={"different": "payload"}, headers={"Another-Header": "Test2"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_update_payment_empty_body():
    response = client.post("/update-payment/empty_test")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_update_payment_query_params():
    response = client.post("/update-payment/query_test?param1=value1&param2=value2", json={"test": "data"})
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
