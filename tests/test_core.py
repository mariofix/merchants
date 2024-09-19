import pytest  # noqa
from fastapi.testclient import TestClient

from merchants.FastapiApp import app

# Create a test client
client = TestClient(app)


# Test root endpoint
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
