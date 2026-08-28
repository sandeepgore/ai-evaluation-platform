from typing import Any

from app.services.evaluators.base import (
    EvaluationScore,
    Evaluator,
    EvaluatorMetadata,
)
from app.services.judge import (
    JudgeConfiguration,
    JudgeService,
)
from app.services.model_gateway.base import ModelGateway


class LLMJudgeEvaluator(Evaluator):
    """
    LLM-as-a-Judge evaluator.

    Delegates judge execution to JudgeService so that:

    - prompt construction
    - judge model configuration
    - response parsing
    - score validation
    - judge metadata

    are implemented in one canonical place.

    The evaluator remains responsible for adapting the generic
    JudgeResult into the platform's EvaluationScore contract.
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

        The evaluator registry can contain a reusable
        LLMJudgeEvaluator instance while each evaluation run
        can provide its own dedicated judge model.
        """

        self.model_gateway = model_gateway
        self.model_configuration = model_configuration or {}

    def _build_judge_configuration(self) -> JudgeConfiguration:
        """
        Build the canonical JudgeConfiguration from the evaluator
        model configuration.

        Existing evaluator configuration remains supported so that
        the engine and evaluator registry do not need to change.
        """

        configuration = dict(self.model_configuration)

        model = configuration.pop(
            "model",
            "llama3.2:3b",
        )

        provider = configuration.pop(
            "provider",
            "ollama",
        )

        base_url = configuration.pop(
            "base_url",
            None,
        )

        timeout = configuration.pop(
            "timeout",
            60.0,
        )

        temperature = configuration.pop(
            "temperature",
            None,
        )

        criteria = configuration.pop(
            "criteria",
            (
                "Evaluate the quality of the actual output against the "
                "expected output. Consider correctness, relevance, "
                "completeness, clarity, and faithfulness."
            ),
        )

        min_score = configuration.pop(
            "min_score",
            0.0,
        )

        max_score = configuration.pop(
            "max_score",
            1.0,
        )

        # response_format is controlled by JudgeService.
        configuration.pop(
            "response_format",
            None,
        )

        return JudgeConfiguration(
            provider=provider,
            model=model,
            base_url=base_url,
            timeout=float(timeout),
            criteria=criteria,
            min_score=float(min_score),
            max_score=float(max_score),
            temperature=temperature,
            extra_configuration=configuration,
        )

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
                feedback="LLM judge model gateway is not configured.",
            )

        configuration = self._build_judge_configuration()

        judge = JudgeService(
            model_gateway=self.model_gateway,
            configuration=configuration,
        )

        try:
            result = await judge.evaluate(
                input_text=self._extract_input(context),
                expected_output=expected_output,
                actual_output=actual_output,
                context=self._extract_context(context),
            )

        except ValueError as exc:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback=str(exc),
            )

        metadata = dict(result.metadata or {})

        return EvaluationScore(
            metric=self.name,
            score=result.score,
            feedback=result.feedback or "",
            metadata={
                **metadata,
                "judge_reasoning": result.reasoning,
                "judge_output": result.raw_output,
            },
        )

    @staticmethod
    def _extract_input(
        context: dict[str, Any] | None,
    ) -> str | None:
        """
        Extract the input/query from evaluator context.
        """

        if not context:
            return None

        value = context.get("input") or context.get("query")

        return value if isinstance(value, str) else None

    @staticmethod
    def _extract_context(
        context: dict[str, Any] | None,
    ) -> Any:
        """
        Extract supporting context while preserving its structure.
        """

        if not context:
            return None

        return (
            context.get("context")
            or context.get("retrieved_context")
            or context.get("reference_context")
        )
