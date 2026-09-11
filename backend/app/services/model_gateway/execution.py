from enum import Enum


class ModelExecutionMode(str, Enum):
    HOSTED = "hosted"
    LOCAL = "local"
    ENDPOINT = "endpoint"
