import uuid

from pydantic import BaseModel

# from .settings import settings


class DummyPayment(BaseModel):
    transaction_id: uuid.UUID


def create_payment() -> DummyPayment: ...
