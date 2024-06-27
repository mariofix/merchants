from dataclasses import dataclass


@dataclass
class ModelStatus:
    CREATED: str = "Created"
    PROCESSING: str = "Processing"
    ERROR: str = "Error"
    REJECTED: str = "Rejected"
    COMPLETED: str = "Completed"
    REFUNDED: str = "Refunded"
    REVERSED: str = "Reversed"
