from typing import Any


class EvaluationCostService:
    """
    Calculates model inference cost from token usage and pricing.

    Pricing is expressed as USD per 1,000,000 tokens.
    """

    DEFAULT_CURRENCY = "USD"

    @staticmethod
    def calculate(
        *,
        input_tokens: int,
        output_tokens: int,
        input_price_per_million: float = 0.0,
        output_price_per_million: float = 0.0,
        currency: str = DEFAULT_CURRENCY,
    ) -> dict[str, Any]:
        """
        Calculate input, output, and total model inference cost.
        """

        input_cost = (input_tokens / 1_000_000) * input_price_per_million

        output_cost = (output_tokens / 1_000_000) * output_price_per_million

        total_cost = input_cost + output_cost

        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "currency": currency,
        }
