from enum import Enum


class ModelStatus(Enum):
    """
    Enumeration of possible payment statuses.
    """

    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    ERROR = "ERROR"
    REJECTED = "REJEDTED"
    COMPLETED = "COMPLETED"
    FULL_REFUND = "FULL_REFUND"
    PARTIAL_REFUND = "PARTIAL_REFUND"
    REVERSED = "REVERSED"
