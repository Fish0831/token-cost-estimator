import json
from dataclasses import dataclass
from pathlib import Path

MODELS_PATH = Path(__file__).parent / "data" / "models.json"


@dataclass
class ModelPrice:
    name: str
    vendor: str
    input_price: float
    output_price: float


def load_models() -> dict[str, ModelPrice]:
    with open(MODELS_PATH, encoding="utf-8") as f:
        raw = json.load(f)

    models = {}
    for name, info in raw.items():
        models[name] = ModelPrice(
            name=name,
            vendor=info["vendor"],
            input_price=info["input_price"],
            output_price=info["output_price"],
        )
    return models


def check_non_negative(name: str, value: int) -> None:
    if value < 0:
        raise ValueError(f"{name} must be >= 0, got {value}")


def estimate_monthly_cost(
    model: str,
    requests_per_day: int,
    input_tokens: int,
    output_tokens: int,
    days: int = 30,
) -> float:
    models = load_models()
    if model not in models:
        available = ", ".join(models)
        raise ValueError(f"Unknown model: '{model}'. Available: {available}")

    check_non_negative("requests_per_day", requests_per_day)
    check_non_negative("input_tokens", input_tokens)
    check_non_negative("output_tokens", output_tokens)
    check_non_negative("days", days)

    price = models[model]

    cost_per_request = (
        input_tokens * price.input_price
        + output_tokens * price.output_price
    ) / 1_000_000

    return cost_per_request * requests_per_day * days


def compare_models(
    requests_per_day: int,
    input_tokens: int,
    output_tokens: int,
    days: int = 30,
) -> list[tuple[str, float]]:
    results = []
    for name in load_models():
        cost = estimate_monthly_cost(
            name, requests_per_day, input_tokens, output_tokens, days
        )
        results.append((name, cost))

    results.sort(key=lambda item: item[1])
    return results


if __name__ == "__main__":
    for name, cost in compare_models(1000, 800, 300):
        print(f"{name:<20} ${cost:>8.2f}")
