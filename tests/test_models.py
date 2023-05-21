from typing import Literal, get_args, get_origin

from merchants.core.orm import sqla


def test_Payment_status_type():
    assert get_origin(sqla.PaymentStatus) is Literal

def test_Payment_status_values():
    expected_values = ["Created", "Paid", "Rejected"]
    for v in expected_values:
        assert v in get_args(sqla.PaymentStatus)
