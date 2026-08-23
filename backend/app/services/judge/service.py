import json
from typing import Any

from app.services.judge.configuration import JudgeConfiguration
from app.services.judge.result import JudgeResult
from app.services.model_gateway import ModelGateway


class JudgeService:
    """
    Executes an LLM-based evaluation judge.

    The judge communicates through ModelGateway and therefore remains
    independent of the underlying model provider.
    """

    def __init__(
        self,
        model_gateway: ModelGateway,
        configuration: JudgeConfiguration,
    ) -> None:
        self.model_gateway = model_gateway
        self.configuration = configuration

    async def evaluate(
        self,
        *,
        input_text: str | None = None,
        expected_output: str | None = None,
        actual_output: str,
        context: Any = None,
    ) -> JudgeResult:
        """
        Evaluate an actual model output using the configured judge model.
        """

        if not actual_output:
            raise ValueError("Actual output must not be empty.")

        prompt = self._build_prompt(
            input_text=input_text,
            expected_output=expected_output,
            actual_output=actual_output,
            context=context,
        )

        model_configuration = self.configuration.to_model_configuration()

        response = await self.model_gateway.generate(
            prompt=prompt,
            configuration=model_configuration,
        )

        return self._parse_response(
            response.output,
        )

    def _build_prompt(
        self,
        *,
        input_text: str | None,
        expected_output: str | None,
        actual_output: str,
        context: Any,
    ) -> str:
        """
        Build a structured judge prompt.
        """

        expected_section = (
            expected_output if expected_output is not None else "No expected output was provided."
        )

        context_section = (
            self._serialize_context(context) if context is not None else "No context was provided."
        )

        input_section = input_text if input_text is not None else "No input was provided."

        return f"""
You are an AI evaluation judge.

Your task is to evaluate the actual model output.

Evaluation criteria:
{self.configuration.criteria}

Return ONLY valid JSON.

The JSON must contain:

{{
  "score": <number between 0 and 1>,
  "feedback": "<short explanation>",
  "reasoning": "<brief reasoning>"
}}

Input:
{input_section}

Expected output:
{expected_section}

Context:
{context_section}

Actual output:
{actual_output}
""".strip()

    @staticmethod
    def _serialize_context(context: Any) -> str:
        """
        Serialize evaluation context safely.
        """

        if isinstance(context, str):
            return context

        try:
            return json.dumps(
                context,
                ensure_ascii=False,
                default=str,
            )
        except (TypeError, ValueError):
            return str(context)

    def _parse_response(
        self,
        raw_output: str,
    ) -> JudgeResult:
        """
        Parse and validate the judge model response.
        """

        if not raw_output or not raw_output.strip():
            raise ValueError("Judge model returned an empty response.")

        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise ValueError("Judge model returned invalid JSON.") from exc

        if not isinstance(data, dict):
            raise ValueError("Judge response must be a JSON object.")

        score = data.get("score")

        if isinstance(score, bool) or not isinstance(
            score,
            (int, float),
        ):
            raise ValueError("Judge response 'score' must be a number.")

        score = float(score)

        if not self.configuration.min_score <= score <= self.configuration.max_score:
            raise ValueError(
                f"Judge score must be between "
                f"{self.configuration.min_score} and "
                f"{self.configuration.max_score}."
            )

        feedback = data.get("feedback")

        if feedback is not None and not isinstance(feedback, str):
            feedback = str(feedback)

        reasoning = data.get("reasoning")

        if reasoning is not None and not isinstance(reasoning, str):
            reasoning = str(reasoning)

        return JudgeResult(
            score=score,
            feedback=feedback,
            reasoning=reasoning,
            metadata={
                "judge_model": self.configuration.model,
                "judge_provider": self.configuration.provider,
            },
            raw_output=raw_output,
        )
