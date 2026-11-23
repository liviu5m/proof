from decimal import ROUND_HALF_UP, Decimal


def calculate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    input_cost_per_1m: Decimal | None,
    output_cost_per_1m: Decimal | None,
) -> Decimal | None:
    """Return cost in USD, or None if prices unknown."""
    if input_cost_per_1m is None or output_cost_per_1m is None:
        return None
    if prompt_tokens == 0 and completion_tokens == 0:
        return Decimal("0")

    cost = (
        (Decimal(prompt_tokens) * input_cost_per_1m) +
        (Decimal(completion_tokens) * output_cost_per_1m)
    ) / Decimal("1_000_000")
    return cost.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
