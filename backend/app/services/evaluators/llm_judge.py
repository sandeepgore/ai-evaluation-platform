from typing import Any

from app.services.evaluators.base import (
    EvaluationScore,
    Evaluator,
    EvaluatorMetadata,
)
from app.services.model_gateway.base import ModelGateway


class LLMJudgeEvaluator(Evaluator):
    """
    LLM-as-a-Judge evaluator.

    Uses a dedicated language model to evaluate the quality of a
    generated response.

    The evaluator itself is provider-independent and depends only
    on the ModelGateway abstraction.

    The model gateway can be supplied during construction or bound
    later using set_model_gateway(). This allows the evaluator to be
    registered globally for discovery while the actual judge model
    is selected per evaluation run.
    """

    def __init__(
        self,
        model_gateway: ModelGateway | None = None,
        model_configuration: dict[str, Any] | None = None,
    ) -> None:
        self.model_gateway = model_gateway
        self.model_configuration = model_configuration or {}

    @property
    def name(self) -> str:
        return "llm_judge"

    @property
    def metadata(self) -> EvaluatorMetadata:
        return EvaluatorMetadata(
            category="llm_judge",
            description=(
                "Uses a separate language model to evaluate the quality "
                "of a generated response against the input, reference, "
                "and optional supporting context."
            ),
            required_inputs=("actual_output",),
            requires_reference=False,
            requires_context=False,
            requires_llm=True,
            applicable_to=(
                "text",
                "rag",
                "conversation",
            ),
            tags=(
                "llm",
                "judge",
                "model-based",
                "semantic",
            ),
        )

    def set_model_gateway(
        self,
        model_gateway: ModelGateway,
        model_configuration: dict[str, Any] | None = None,
    ) -> None:
        """
        Bind the dedicated judge model gateway.

        The evaluator registry can contain a single reusable
        LLMJudgeEvaluator instance while each evaluation run can
        provide its own dedicated judge model.
        """
        self.model_gateway = model_gateway
        self.model_configuration = model_configuration or {}

    @staticmethod
    def _build_prompt(
        *,
        actual_output: str,
        expected_output: str | None,
        context: dict[str, Any] | None,
    ) -> str:
        """
        Build the prompt sent to the judge model.
        """

        input_text = ""

        if context:
            input_value = context.get("input") or context.get("query")

            if isinstance(input_value, str):
                input_text = input_value.strip()

        context_text = ""

        if context:
            context_value = (
                context.get("context")
                or context.get("retrieved_context")
                or context.get("reference_context")
            )

            if isinstance(context_value, str):
                context_text = context_value.strip()

            elif isinstance(context_value, (list, tuple)):
                context_text = "\n".join(
                    item.strip() for item in context_value if isinstance(item, str) and item.strip()
                )

        reference_section = (
            expected_output.strip()
            if isinstance(expected_output, str) and expected_output.strip()
            else "No reference answer was provided."
        )

        input_section = input_text if input_text else "No input/query was provided."

        context_section = context_text if context_text else "No supporting context was provided."

        return f"""
You are an expert evaluator judging the quality of an AI-generated response.

Evaluate the response using the following information.

INPUT / QUERY:
{input_section}

REFERENCE ANSWER:
{reference_section}

SUPPORTING CONTEXT:
{context_section}

GENERATED RESPONSE:
{actual_output.strip()}

Evaluate the generated response for:

1. Correctness
2. Relevance
3. Completeness
4. Clarity
5. Faithfulness to the provided information

Return ONLY valid JSON using exactly this structure:

{{
    "score": 0.0,
    "feedback": "brief explanation"
}}

Rules:

- score must be a number between 0.0 and 1.0
- 0.0 means completely unacceptable
- 1.0 means excellent
- Do not include markdown
- Do not include additional JSON fields
""".strip()

    @staticmethod
    def _parse_score(
        response: str,
    ) -> tuple[float, str]:
        """
        Parse the judge model response.

        The model is instructed to return JSON, but LLMs may
        occasionally return valid JSON surrounded by whitespace,
        Markdown code fences, or short explanatory text.

        Expected payload:

        {
            "score": 0.85,
            "feedback": "..."
        }
        """

        import json

        if not isinstance(response, str) or not response.strip():
            raise ValueError("LLM judge returned an empty response.")

        cleaned = response.strip()

        # ----------------------------------------------------------
        # Handle Markdown code fences.
        #
        # Example:
        #
        # ```json
        # {
        #     "score": 0.9,
        #     "feedback": "Good response."
        # }
        # ```
        # ----------------------------------------------------------

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(lines).strip()

            # Handle a language identifier that may remain after
            # removing the opening fence.
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()

        # ----------------------------------------------------------
        # First attempt: strict JSON parsing.
        #
        # This remains the preferred path because it ensures that
        # normal valid JSON is handled without modification.
        # ----------------------------------------------------------

        try:
            data = json.loads(cleaned)

        except json.JSONDecodeError:
            # ------------------------------------------------------
            # Fallback:
            #
            # Some LLMs return valid JSON together with explanatory
            # text, for example:
            #
            # Here is the evaluation:
            # {"score": 0.9, "feedback": "..."}
            #
            # JSONDecoder.raw_decode() lets us parse the JSON object
            # without using a fragile regex.
            # ------------------------------------------------------

            decoder = json.JSONDecoder()

            start = cleaned.find("{")

            if start == -1:
                raise ValueError("LLM judge returned invalid JSON.")

            try:
                data, _ = decoder.raw_decode(cleaned[start:])

            except json.JSONDecodeError as exc:
                raise ValueError("LLM judge returned invalid JSON.") from exc

        # ----------------------------------------------------------
        # Validate response structure.
        # ----------------------------------------------------------

        if not isinstance(data, dict):
            raise ValueError("LLM judge response must be a JSON object.")

        score = data.get("score")
        feedback = data.get("feedback")

        # ----------------------------------------------------------
        # Validate score.
        # ----------------------------------------------------------

        if not isinstance(score, (int, float)) or isinstance(
            score,
            bool,
        ):
            raise ValueError("LLM judge response must contain a numeric 'score'.")

        score = float(score)

        if not 0.0 <= score <= 1.0:
            raise ValueError("LLM judge score must be between 0.0 and 1.0.")

        # ----------------------------------------------------------
        # Feedback is optional from the parser perspective.
        # ----------------------------------------------------------

        if not isinstance(feedback, str):
            feedback = ""

        return score, feedback

    async def evaluate(
        self,
        *,
        expected_output: str | None,
        actual_output: str | None,
        context: dict[str, Any] | None = None,
    ) -> EvaluationScore:
        """
        Evaluate generated output using the dedicated LLM judge.
        """

        if actual_output is None:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Actual output is missing.",
            )

        if not actual_output.strip():
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Actual output is empty.",
            )

        if self.model_gateway is None:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback=("LLM judge model gateway is not configured."),
            )

        prompt = self._build_prompt(
            actual_output=actual_output,
            expected_output=expected_output,
            context=context,
        )

        judge_configuration = dict(self.model_configuration)
        judge_configuration["response_format"] = "json"

        model_response = await self.model_gateway.generate(
            prompt=prompt,
            configuration=judge_configuration,
        )

        try:
            score, feedback = self._parse_score(
                model_response.output,
            )

        except ValueError as exc:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback=str(exc),
                metadata={
                    "judge_output": model_response.output,
                },
            )

        trace = model_response.trace or {}

        return EvaluationScore(
            metric=self.name,
            score=score,
            feedback=feedback,
            metadata={
                "judge_model": trace.get("model"),
                "judge_provider": trace.get("provider"),
                "judge_latency_ms": model_response.latency_ms,
                "judge_input_tokens": model_response.input_tokens,
                "judge_output_tokens": model_response.output_tokens,
                "judge_total_tokens": model_response.total_tokens,
                "judge_output": model_response.output,
            },
        )
