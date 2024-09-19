import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from merchants.database import engine
from merchants.FastapiApp import app

# Create a test client
client = TestClient(app)


# Mock database session
@pytest.fixture
def mock_db():
    with Session(engine) as session:
        yield session


# Test root endpoint
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
