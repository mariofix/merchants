from typing import Literal

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy_utils import generic_repr

from merchants.core.orm.sqla import PaymentMixin

SQLALCHEMY_DATABASE_URL = "sqlite:///./examples/sqlalchemy/db.sqlite3"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


@generic_repr
class Purchases(Base, PaymentMixin):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True)


Base.metadata.create_all(bind=engine)

with SessionLocal() as session:
    pur = Purchases(provider="dummy")
    session.add(pur)
    session.commit()

    print(pur.make_payment())
