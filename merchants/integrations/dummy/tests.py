import datetime
from decimal import Decimal

import pytest
from sqlalchemy import Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, mapped_column  # Mapped

from merchants.core.schemas import ModelStatus
from merchants.orm.sqla import PaymentMixin


class Base(DeclarativeBase):
    pass


class TestPayment(Base, PaymentMixin):
    __tablename__ = "test_payments"
    id = mapped_column(Integer, primary_key=True)


@pytest.fixture(scope="module")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def sample_payment(db_session):
    payment = TestPayment(account="test_account", amount=Decimal("100.00"), currency="USD", status=ModelStatus.CREATED)
    db_session.add(payment)
    db_session.commit()
    return payment


def test_payment_creation(sample_payment):
    assert sample_payment.account == "test_account"
    assert sample_payment.amount == Decimal("100.00")
    assert sample_payment.currency == "USD"
    assert sample_payment.status == ModelStatus.CREATED


def test_payment_status_enum():
    assert ModelStatus.CREATED.value == "CREATED"
    assert ModelStatus.COMPLETED.value == "COMPLETED"
    assert len(ModelStatus) == 8  # Ensure all statuses are present


def test_make_payment(sample_payment, mocker):
    mock_make_payment = mocker.patch.object(TestPayment, "make_payment")

    new_payment = TestPayment(
        account="new_account", amount=Decimal("50.00"), currency="EUR", status=ModelStatus.CREATED
    )

    db_session.add(new_payment)
    db_session.commit()

    mock_make_payment.assert_called_once()


def test_payment_update(sample_payment, db_session):
    sample_payment.status = ModelStatus.COMPLETED
    db_session.commit()

    updated_payment = db_session.get(TestPayment, sample_payment.id)
    assert updated_payment.status == ModelStatus.COMPLETED


def test_extra_info_and_response_json(sample_payment, db_session):
    sample_payment.extra_info = {"key": "value"}
    sample_payment.response = {"status": "success"}
    db_session.commit()

    updated_payment = db_session.get(TestPayment, sample_payment.id)
    assert updated_payment.extra_info == {"key": "value"}
    assert updated_payment.response == {"status": "success"}


def test_automatic_timestamps(db_session):
    payment = TestPayment(
        account="timestamp_test", amount=Decimal("75.00"), currency="GBP", status=ModelStatus.CREATED
    )
    db_session.add(payment)
    db_session.commit()

    assert payment.created is not None
    assert isinstance(payment.created, datetime.datetime)

    original_modified = payment.modified
    payment.amount = Decimal("80.00")
    db_session.commit()

    assert payment.modified > original_modified
