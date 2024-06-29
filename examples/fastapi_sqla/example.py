from decimal import Decimal

from fastapi import FastAPI
from icecream import ic
from sqlalchemy import create_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, sessionmaker
from starlette_admin.contrib.sqla import Admin, ModelView

from merchants.orm.sqla import PaymentMixin

SQLALCHEMY_DATABASE_URL = "sqlite:///./examples/fastapi_sqla/merchants.sqlite3"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Payment(PaymentMixin, Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)

    def make_payment(self):
        ic(self)


Base.metadata.create_all(engine)

session = SessionLocal()

payment = Payment(account="timestamp_test", amount=Decimal("100.00"), currency="USD", status="CREATED")

session.add(payment)
session.commit()


app = FastAPI()
admin = Admin(engine, title="merchants: SQLAlchemy")
admin.add_view(ModelView(Payment))
admin.mount_to(app)
