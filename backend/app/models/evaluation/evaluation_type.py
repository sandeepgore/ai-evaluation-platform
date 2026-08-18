from enum import Enum


class EvaluationType(str, Enum):
    TEXT = "text"
    RAG = "rag"
    CONVERSATION = "conversation"
    SAFETY = "safety"
