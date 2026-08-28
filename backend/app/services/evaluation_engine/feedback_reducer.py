import json
from typing import Any

from app.schemas.evaluation.summary import EvaluationRunFeedbackResponse
from app.services.model_gateway import ModelGateway


class EvaluationFeedbackReducer:
    """
    Reduces evaluator feedback into one rolling qualitative summary.

    This service:
        - does not access Redis
        - does not access PostgreSQL
        - does not calculate evaluation scores
        - only performs qualitative feedback reduction

    The reducer receives:
        - an optional previous rolling feedback summary
        - a bounded set of new evaluator feedback items

    It returns:
        EvaluationRunFeedbackResponse

    The evaluator_feedback field is intentionally kept empty for the
    rolling reducer so the state remains bounded.
    """

    DEFAULT_TIMEOUT_SECONDS = 60.0

    def __init__(
        self,
        model_gateway: ModelGateway,
        *,
        model: str,
        provider: str,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.model_gateway = model_gateway
        self.model = model
        self.provider = provider
        self.timeout = timeout

    async def reduce(
        self,
        *,
        current_feedback: EvaluationRunFeedbackResponse | None,
        feedback_items: list[dict[str, Any]],
    ) -> EvaluationRunFeedbackResponse:
        """
        Produce the next rolling qualitative feedback summary.

        The first reduction can receive up to 20 new feedback items.

        Subsequent reductions receive:
            - the previous reduced feedback
            - up to 19 new feedback items
        """

        normalized_feedback = self._normalize_feedback_items(
            feedback_items,
        )

        if current_feedback is None and not normalized_feedback:
            return self._empty_feedback()

        if current_feedback is not None:
            current_feedback = self._normalize_current_feedback(
                current_feedback,
            )

        prompt = self._build_prompt(
            current_feedback=current_feedback,
            feedback_items=normalized_feedback,
        )

        response = await self.model_gateway.generate(
            prompt=prompt,
            configuration={
                "model": self.model,
                "provider": self.provider,
                "timeout": self.timeout,
                "response_format": "json",
            },
        )

        return self._parse_response(
            response.output,
        )

    @staticmethod
    def _empty_feedback() -> EvaluationRunFeedbackResponse:
        return EvaluationRunFeedbackResponse(
            overall="",
            strengths=[],
            weaknesses=[],
            patterns=[],
            recommendations=[],
            evaluator_feedback=[],
        )

    @staticmethod
    def _normalize_current_feedback(
        feedback: EvaluationRunFeedbackResponse,
    ) -> EvaluationRunFeedbackResponse:
        return EvaluationRunFeedbackResponse(
            overall=feedback.overall.strip(),
            strengths=[
                item.strip()
                for item in feedback.strengths
                if isinstance(item, str) and item.strip()
            ],
            weaknesses=[
                item.strip()
                for item in feedback.weaknesses
                if isinstance(item, str) and item.strip()
            ],
            patterns=[
                item.strip() for item in feedback.patterns if isinstance(item, str) and item.strip()
            ],
            recommendations=[
                item.strip()
                for item in feedback.recommendations
                if isinstance(item, str) and item.strip()
            ],
            evaluator_feedback=[],
        )

    @staticmethod
    def _normalize_feedback_items(
        feedback_items: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []

        for item in feedback_items:
            if not isinstance(item, dict):
                continue

            result_id = item.get("id")
            feedback = item.get("feedback")

            if not isinstance(result_id, str):
                continue

            if not isinstance(feedback, str):
                continue

            feedback = " ".join(feedback.strip().split())

            if not feedback:
                continue

            normalized.append(
                {
                    "id": result_id,
                    "feedback": feedback,
                }
            )

        return normalized

    @staticmethod
    def _build_prompt(
        *,
        current_feedback: EvaluationRunFeedbackResponse | None,
        feedback_items: list[dict[str, str]],
    ) -> str:
        current_feedback_json = json.dumps(
            (
                current_feedback.model_dump(
                    exclude={"evaluator_feedback"},
                )
                if current_feedback is not None
                else None
            ),
            ensure_ascii=False,
            indent=2,
        )

        feedback_json = json.dumps(
            feedback_items,
            ensure_ascii=False,
            indent=2,
        )

        return f"""
You are a qualitative feedback reducer for an AI evaluation platform.

Your task is to maintain a concise rolling summary of evaluator feedback.

The previous rolling feedback summary is:

{current_feedback_json}

New evaluator feedback items are:

{feedback_json}

Produce the next rolling summary.

Requirements:

- Preserve important recurring strengths.
- Preserve important recurring weaknesses.
- Preserve recurring patterns when supported by the evidence.
- Preserve actionable recommendations when supported by the evidence.
- Remove redundant wording.
- Combine similar observations.
- Do not invent facts, metrics, scores, or evaluator conclusions.
- Do not calculate or modify any numerical evaluation scores.
- Do not include raw evaluator feedback in the output.
- Keep the result concise enough to be used in another reduction step.

Return ONLY valid JSON with exactly this structure:

{{
  "overall": "overall qualitative assessment",
  "strengths": [
    "strength"
  ],
  "weaknesses": [
    "weakness"
  ],
  "patterns": [
    "recurring pattern"
  ],
  "recommendations": [
    "actionable recommendation"
  ]
}}
""".strip()

    @staticmethod
    def _parse_response(
        raw_output: str,
    ) -> EvaluationRunFeedbackResponse:
        if not raw_output or not raw_output.strip():
            raise ValueError("Feedback reducer returned an empty response.")

        cleaned = raw_output.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(lines).strip()

            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError("Feedback reducer returned invalid JSON.") from exc

        if not isinstance(data, dict):
            raise ValueError("Feedback reducer response must be a JSON object.")

        return EvaluationRunFeedbackResponse(
            overall=(
                " ".join(data.get("overall", "").strip().split())
                if isinstance(data.get("overall"), str)
                else ""
            ),
            strengths=EvaluationFeedbackReducer._normalize_string_list(
                data.get("strengths"),
            ),
            weaknesses=EvaluationFeedbackReducer._normalize_string_list(
                data.get("weaknesses"),
            ),
            patterns=EvaluationFeedbackReducer._normalize_string_list(
                data.get("patterns"),
            ),
            recommendations=EvaluationFeedbackReducer._normalize_string_list(
                data.get("recommendations"),
            ),
            evaluator_feedback=[],
        )

    @staticmethod
    def _normalize_string_list(
        value: Any,
    ) -> list[str]:
        if not isinstance(value, list):
            return []

        normalized: list[str] = []

        for item in value:
            if not isinstance(item, str):
                continue

            item = " ".join(item.strip().split())

            if item:
                normalized.append(item)

        return normalized
