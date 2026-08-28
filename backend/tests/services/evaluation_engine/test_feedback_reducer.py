import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.schemas.evaluation.summary import EvaluationRunFeedbackResponse
from app.services.evaluation_engine.feedback_reducer import (
    EvaluationFeedbackReducer,
)


def make_response(output: str):
    return SimpleNamespace(output=output)


def make_feedback(
    *,
    overall="Responses are generally relevant.",
    strengths=None,
    weaknesses=None,
    patterns=None,
    recommendations=None,
):
    return EvaluationRunFeedbackResponse(
        overall=overall,
        strengths=strengths or ["Good relevance."],
        weaknesses=weaknesses or ["Some responses lack detail."],
        patterns=patterns or ["Responses are often brief."],
        recommendations=recommendations or ["Provide more supporting detail."],
        evaluator_feedback=[],
    )


@pytest.fixture
def model_gateway():
    gateway = AsyncMock()
    return gateway


@pytest.fixture
def reducer(model_gateway):
    return EvaluationFeedbackReducer(
        model_gateway=model_gateway,
        model="qwen2.5:3b",
        provider="ollama",
    )


class TestEvaluationFeedbackReducer:
    def test_normalize_feedback_items(self):
        result = EvaluationFeedbackReducer._normalize_feedback_items(
            [
                {
                    "id": "1",
                    "feedback": "  first   feedback  ",
                },
                {
                    "id": "2",
                    "feedback": "\nsecond\tfeedback\n",
                },
            ]
        )

        assert result == [
            {
                "id": "1",
                "feedback": "first feedback",
            },
            {
                "id": "2",
                "feedback": "second feedback",
            },
        ]

    def test_normalize_feedback_ignores_invalid_items(self):
        result = EvaluationFeedbackReducer._normalize_feedback_items(
            [
                None,
                {},
                {
                    "id": "missing-feedback",
                },
                {
                    "feedback": "missing-id",
                },
                {
                    "id": 123,
                    "feedback": "invalid id",
                },
                {
                    "id": "empty-feedback",
                    "feedback": "   ",
                },
                {
                    "id": "valid",
                    "feedback": "valid feedback",
                },
            ]
        )

        assert result == [
            {
                "id": "valid",
                "feedback": "valid feedback",
            }
        ]

    @pytest.mark.asyncio
    async def test_reduce_empty_input_returns_empty_feedback(
        self,
        reducer,
        model_gateway,
    ):
        result = await reducer.reduce(
            current_feedback=None,
            feedback_items=[],
        )

        assert isinstance(
            result,
            EvaluationRunFeedbackResponse,
        )

        assert result.overall == ""
        assert result.strengths == []
        assert result.weaknesses == []
        assert result.patterns == []
        assert result.recommendations == []
        assert result.evaluator_feedback == []

        model_gateway.generate.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_reduce_generates_initial_feedback(
        self,
        reducer,
        model_gateway,
    ):
        model_gateway.generate = AsyncMock(
            return_value=make_response(
                json.dumps(
                    {
                        "overall": ("Responses are generally relevant but often incomplete."),
                        "strengths": [
                            "Good relevance.",
                        ],
                        "weaknesses": [
                            "Limited completeness.",
                        ],
                        "patterns": [
                            "Answers are often brief.",
                        ],
                        "recommendations": [
                            "Provide more supporting detail.",
                        ],
                    }
                )
            )
        )

        items = [
            {
                "id": str(uuid4()),
                "feedback": "Response is relevant.",
            },
            {
                "id": str(uuid4()),
                "feedback": "Response lacks completeness.",
            },
        ]

        result = await reducer.reduce(
            current_feedback=None,
            feedback_items=items,
        )

        assert result.overall == ("Responses are generally relevant but often incomplete.")

        assert result.strengths == [
            "Good relevance.",
        ]

        assert result.weaknesses == [
            "Limited completeness.",
        ]

        assert result.patterns == [
            "Answers are often brief.",
        ]

        assert result.recommendations == [
            "Provide more supporting detail.",
        ]

        assert result.evaluator_feedback == []

        model_gateway.generate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reduce_uses_previous_feedback(
        self,
        reducer,
        model_gateway,
    ):
        model_gateway.generate = AsyncMock(
            return_value=make_response(
                json.dumps(
                    {
                        "overall": "Good relevance with limited detail.",
                        "strengths": ["Good relevance."],
                        "weaknesses": ["Limited detail."],
                        "patterns": ["Responses are often brief."],
                        "recommendations": [
                            "Add supporting detail.",
                        ],
                    }
                )
            )
        )

        previous_feedback = make_feedback(
            overall="Responses are generally relevant.",
        )

        await reducer.reduce(
            current_feedback=previous_feedback,
            feedback_items=[
                {
                    "id": "21",
                    "feedback": "The answer lacks supporting detail.",
                }
            ],
        )

        prompt = model_gateway.generate.await_args.kwargs["prompt"]

        assert "Responses are generally relevant." in prompt
        assert "The answer lacks supporting detail." in prompt

    @pytest.mark.asyncio
    async def test_reduce_uses_expected_configuration(
        self,
        reducer,
        model_gateway,
    ):
        model_gateway.generate = AsyncMock(
            return_value=make_response(
                json.dumps(
                    {
                        "overall": "Summary.",
                        "strengths": [],
                        "weaknesses": [],
                        "patterns": [],
                        "recommendations": [],
                    }
                )
            )
        )

        await reducer.reduce(
            current_feedback=None,
            feedback_items=[
                {
                    "id": "1",
                    "feedback": "Feedback.",
                }
            ],
        )

        configuration = model_gateway.generate.await_args.kwargs["configuration"]

        assert configuration["model"] == "qwen2.5:3b"
        assert configuration["provider"] == "ollama"
        assert configuration["timeout"] == 60.0
        assert configuration["response_format"] == "json"

    @pytest.mark.asyncio
    async def test_reduce_includes_result_ids_in_prompt(
        self,
        reducer,
        model_gateway,
    ):
        model_gateway.generate = AsyncMock(
            return_value=make_response(
                json.dumps(
                    {
                        "overall": "Summary.",
                        "strengths": [],
                        "weaknesses": [],
                        "patterns": [],
                        "recommendations": [],
                    }
                )
            )
        )

        await reducer.reduce(
            current_feedback=None,
            feedback_items=[
                {
                    "id": "result-123",
                    "feedback": "Feedback.",
                }
            ],
        )

        prompt = model_gateway.generate.await_args.kwargs["prompt"]

        assert "result-123" in prompt
        assert "Feedback." in prompt

    @pytest.mark.asyncio
    async def test_reduce_parses_structured_feedback_response(
        self,
        reducer,
        model_gateway,
    ):
        model_gateway.generate = AsyncMock(
            return_value=make_response(
                json.dumps(
                    {
                        "overall": "A concise assessment.",
                        "strengths": [
                            "Strong relevance.",
                        ],
                        "weaknesses": [
                            "Some responses lack detail.",
                        ],
                        "patterns": [
                            "Brief answers are common.",
                        ],
                        "recommendations": [
                            "Provide more detail.",
                        ],
                    }
                )
            )
        )

        result = await reducer.reduce(
            current_feedback=None,
            feedback_items=[
                {
                    "id": "1",
                    "feedback": "Feedback.",
                }
            ],
        )

        assert result == EvaluationRunFeedbackResponse(
            overall="A concise assessment.",
            strengths=[
                "Strong relevance.",
            ],
            weaknesses=[
                "Some responses lack detail.",
            ],
            patterns=[
                "Brief answers are common.",
            ],
            recommendations=[
                "Provide more detail.",
            ],
            evaluator_feedback=[],
        )

    @pytest.mark.asyncio
    async def test_reduce_accepts_markdown_json(
        self,
        reducer,
        model_gateway,
    ):
        model_gateway.generate = AsyncMock(
            return_value=make_response(
                """```json
{
  "overall": "A concise assessment.",
  "strengths": ["Strong relevance."],
  "weaknesses": ["Some responses lack detail."],
  "patterns": ["Brief answers are common."],
  "recommendations": ["Provide more detail."]
}
```"""
            )
        )

        result = await reducer.reduce(
            current_feedback=None,
            feedback_items=[
                {
                    "id": "1",
                    "feedback": "Feedback.",
                }
            ],
        )

        assert result.overall == "A concise assessment."
        assert result.strengths == [
            "Strong relevance.",
        ]
        assert result.weaknesses == [
            "Some responses lack detail.",
        ]
        assert result.patterns == [
            "Brief answers are common.",
        ]
        assert result.recommendations == [
            "Provide more detail.",
        ]
        assert result.evaluator_feedback == []

    @pytest.mark.asyncio
    async def test_reduce_normalizes_structured_feedback(
        self,
        reducer,
        model_gateway,
    ):
        model_gateway.generate = AsyncMock(
            return_value=make_response(
                json.dumps(
                    {
                        "overall": "  Summary   with   extra whitespace  ",
                        "strengths": [
                            "  Good   relevance  ",
                            "",
                            "   ",
                        ],
                        "weaknesses": [
                            "  Limited   detail ",
                        ],
                        "patterns": [
                            " Brief answers ",
                        ],
                        "recommendations": [
                            " Add more context ",
                        ],
                    }
                )
            )
        )

        result = await reducer.reduce(
            current_feedback=None,
            feedback_items=[
                {
                    "id": "1",
                    "feedback": "Feedback.",
                }
            ],
        )

        assert result.overall == ("Summary with extra whitespace")

        assert result.strengths == [
            "Good relevance",
        ]

        assert result.weaknesses == [
            "Limited detail",
        ]

        assert result.patterns == [
            "Brief answers",
        ]

        assert result.recommendations == [
            "Add more context",
        ]

    @pytest.mark.asyncio
    async def test_reduce_never_returns_raw_evaluator_feedback(
        self,
        reducer,
        model_gateway,
    ):
        model_gateway.generate = AsyncMock(
            return_value=make_response(
                json.dumps(
                    {
                        "overall": "Responses are generally relevant.",
                        "strengths": [
                            "Good relevance.",
                        ],
                        "weaknesses": [
                            "Limited detail.",
                        ],
                        "patterns": [
                            "Answers are often brief.",
                        ],
                        "recommendations": [
                            "Provide more detail.",
                        ],
                    }
                )
            )
        )

        result = await reducer.reduce(
            current_feedback=None,
            feedback_items=[
                {
                    "id": "result-1",
                    "feedback": "llm_judge: response is relevant",
                }
            ],
        )

        assert result.evaluator_feedback == []

    @pytest.mark.asyncio
    async def test_reduce_raises_on_empty_response(
        self,
        reducer,
        model_gateway,
    ):
        model_gateway.generate = AsyncMock(return_value=make_response(""))

        with pytest.raises(
            ValueError,
            match="Feedback reducer returned an empty response",
        ):
            await reducer.reduce(
                current_feedback=None,
                feedback_items=[
                    {
                        "id": "1",
                        "feedback": "Feedback.",
                    }
                ],
            )

    @pytest.mark.asyncio
    async def test_reduce_raises_on_invalid_json(
        self,
        reducer,
        model_gateway,
    ):
        model_gateway.generate = AsyncMock(return_value=make_response("not-json"))

        with pytest.raises(
            ValueError,
            match="Feedback reducer returned invalid JSON",
        ):
            await reducer.reduce(
                current_feedback=None,
                feedback_items=[
                    {
                        "id": "1",
                        "feedback": "Feedback.",
                    }
                ],
            )

    @pytest.mark.asyncio
    async def test_reduce_raises_when_response_is_not_object(
        self,
        reducer,
        model_gateway,
    ):
        model_gateway.generate = AsyncMock(
            return_value=make_response(
                json.dumps(
                    [
                        "invalid",
                        "response",
                    ]
                )
            )
        )

        with pytest.raises(
            ValueError,
            match="Feedback reducer response must be a JSON object",
        ):
            await reducer.reduce(
                current_feedback=None,
                feedback_items=[
                    {
                        "id": "1",
                        "feedback": "Feedback.",
                    }
                ],
            )

    @pytest.mark.asyncio
    async def test_reduce_accepts_missing_optional_lists(
        self,
        reducer,
        model_gateway,
    ):
        model_gateway.generate = AsyncMock(
            return_value=make_response(
                json.dumps(
                    {
                        "overall": "Summary.",
                    }
                )
            )
        )

        result = await reducer.reduce(
            current_feedback=None,
            feedback_items=[
                {
                    "id": "1",
                    "feedback": "Feedback.",
                }
            ],
        )

        assert result.overall == "Summary."
        assert result.strengths == []
        assert result.weaknesses == []
        assert result.patterns == []
        assert result.recommendations == []
        assert result.evaluator_feedback == []
