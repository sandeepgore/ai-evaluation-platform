from enum import StrEnum


class DataPolicy(StrEnum):
    """
    Defines how missing evaluation data should be handled.
    """

    STRICT = "strict"
    PARTIAL = "partial"
    THRESHOLD = "threshold"
