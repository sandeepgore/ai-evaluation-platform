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

    Responsibilities:
    - Build the judge prompt.
    - Execute the configured judge model.
    - Parse tolerant LLM JSON responses.
    - Retry malformed structured output once.
    - Validate the judge score.
    - Return a canonical JudgeResult.
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

        A malformed structured response is retried once with a stricter
        JSON-only prompt.
        """

        if not actual_output or not actual_output.strip():
            raise ValueError(
                "Actual output must not be empty.",
            )

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

        try:
            return self._parse_response(
                response.output,
            )

        except ValueError as first_error:
            retry_prompt = self._build_repair_prompt(
                original_prompt=prompt,
                raw_output=response.output,
            )

            retry_response = await self.model_gateway.generate(
                prompt=retry_prompt,
                configuration=model_configuration,
            )

            try:
                result = self._parse_response(
                    retry_response.output,
                )

            except ValueError:
                raise first_error

            return result

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

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

The JSON must contain exactly these fields:

{{
  "score": <number between 0 and 1>,
  "feedback": "<short explanation>",
  "reasoning": "<brief reasoning>"
}}

Important JSON rules:

- Output a single JSON object.
- Do not use Markdown.
- Do not use code fences.
- Do not add text before or after the JSON.
- "score" must be a number.
- "feedback" must be a short string.
- "reasoning" must be a short string.

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
    def _build_repair_prompt(
        *,
        original_prompt: str,
        raw_output: str,
    ) -> str:
        """
        Build a minimal recovery prompt for malformed judge output.

        The model is instructed to preserve its original assessment while
        returning only the required structured JSON object.
        """

        return f"""
You previously attempted to answer the evaluation request below, but your
response was not valid JSON.

Return ONLY one valid JSON object with exactly these fields:

{{
  "score": <number between 0 and 1>,
  "feedback": "<short explanation>",
  "reasoning": "<brief reasoning>"
}}

Rules:

- JSON object only.
- No Markdown.
- No code fences.
- No explanatory text.
- "score" must be numeric.
- "feedback" must be a string.
- "reasoning" must be a string.
- Do not add additional fields.

Original evaluation request:
{original_prompt}

Previous response:
{raw_output}
""".strip()

    @staticmethod
    def _serialize_context(
        context: Any,
    ) -> str:
        """
        Serialize evaluation context safely.
        """

        if isinstance(
            context,
            str,
        ):
            return context

        try:
            return json.dumps(
                context,
                ensure_ascii=False,
                default=str,
            )
        except (TypeError, ValueError):
            return str(context)

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_response(
        self,
        raw_output: str,
    ) -> JudgeResult:
        """
        Parse and validate the judge model response.

        Supported formats include:

        - plain JSON
        - Markdown JSON code fences
        - generic Markdown code fences
        - JSON embedded in surrounding text
        """

        if not raw_output or not raw_output.strip():
            raise ValueError(
                "Judge model returned an empty response.",
            )

        data = self._parse_json_object(
            raw_output.strip(),
        )

        score = data.get("score")

        if isinstance(score, bool) or not isinstance(
            score,
            (int, float),
        ):
            raise ValueError(
                "Judge response 'score' must be a number.",
            )

        score = float(score)

        if not self.configuration.min_score <= score <= self.configuration.max_score:
            raise ValueError(
                f"Judge score must be between "
                f"{self.configuration.min_score} and "
                f"{self.configuration.max_score}."
            )

        feedback = data.get("feedback")

        if feedback is not None and not isinstance(
            feedback,
            str,
        ):
            feedback = str(feedback)

        reasoning = data.get("reasoning")

        if reasoning is not None and not isinstance(
            reasoning,
            str,
        ):
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

    @staticmethod
    def _parse_json_object(
        raw_output: str,
    ) -> dict[str, Any]:
        """
        Extract and parse a JSON object from common LLM response formats.
        """

        # --------------------------------------------------------------
        # 1. Strict JSON
        # --------------------------------------------------------------

        try:
            data = json.loads(
                raw_output,
            )

            if isinstance(
                data,
                dict,
            ):
                return data

            raise ValueError(
                "Judge response must be a JSON object.",
            )

        except json.JSONDecodeError:
            pass

        # --------------------------------------------------------------
        # 2. Markdown code fence
        # --------------------------------------------------------------

        fenced_output = JudgeService._extract_fenced_json(
            raw_output,
        )

        if fenced_output is not None:
            try:
                data = json.loads(
                    fenced_output,
                )

                if isinstance(
                    data,
                    dict,
                ):
                    return data

            except json.JSONDecodeError:
                pass

        # --------------------------------------------------------------
        # 3. Embedded JSON
        # --------------------------------------------------------------

        embedded_output = JudgeService._extract_embedded_json(
            raw_output,
        )

        if embedded_output is not None:
            try:
                data = json.loads(
                    embedded_output,
                )

                if isinstance(
                    data,
                    dict,
                ):
                    return data

            except json.JSONDecodeError:
                pass

        raise ValueError(
            "Judge model returned invalid JSON.",
        )

    @staticmethod
    def _extract_fenced_json(
        value: str,
    ) -> str | None:
        """
        Extract JSON contained inside a Markdown code fence.

        Supports:

        ```json
        {...}
        ```

        and:

        ```
        {...}
        ```
        """

        start = value.find(
            "```",
        )

        if start == -1:
            return None

        end = value.find(
            "```",
            start + 3,
        )

        if end == -1:
            return None

        content = value[start + 3 : end].strip()

        if content.lower().startswith(
            "json",
        ):
            content = content[4:].strip()

        return content or None

    @staticmethod
    def _extract_embedded_json(
        value: str,
    ) -> str | None:
        """
        Extract a JSON object embedded inside surrounding text.

        JSONDecoder.raw_decode() is used instead of simply taking the first
        and last braces, which correctly handles braces appearing inside
        JSON string values.
        """

        decoder = json.JSONDecoder()

        for index, character in enumerate(value):
            if character != "{":
                continue

            try:
                data, _ = decoder.raw_decode(
                    value[index:],
                )

            except json.JSONDecodeError:
                continue

            if isinstance(
                data,
                dict,
            ):
                return json.dumps(
                    data,
                    ensure_ascii=False,
                )

        return None
