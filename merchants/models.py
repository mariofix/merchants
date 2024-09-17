from typing import List, Any, Dict
from sqlmodel import SQLModel, Field
import uuid
from pydantic import EmailStr
import datetime
from sqlalchemy import JSON, Column, event
from slugify import slugify


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=255)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    password: str
    is_active: bool = True
    is_superuser: bool = False
    scopes: List[str] | None = Field(sa_column=Column(JSON, nullable=True))


class UserPublic(SQLModel):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class Broker(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    slug: str | None = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    integration_class: str
    config: Dict[str, Any] | None = Field(sa_column=Column(JSON, nullable=True))
    created_at: datetime.datetime = Field(
        default=datetime.datetime.now,
    )

    # @classmethod
    # def __declare_last__(cls):
    #     event.listen(cls, "before_insert", cls.event_before_insert)

    # @staticmethod
    # def event_before_insert(mapper, connection, target):
    #     """
    #     SQLAlchemy event listener that calls process_payment before inserting a new record.

    #     :param mapper: The Mapper object which is the target of this event
    #     :param connection: The Connection being used for the operation
    #     :param target: The mapped instance being persisted
    #     """
    #     target.slug = slugify(target.name)


class BrokerPublic(SQLModel):
    slug: str


class BrokersPublic(SQLModel):
    count: int
    data: list[BrokerPublic]
