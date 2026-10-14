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


def estimate_monthly_cost(
    model: str,
    requests_per_day: int,
    input_tokens: int,
    output_tokens: int,
    days: int = 30,
) -> float:
    price = load_models()[model]

    cost_per_request = (
        input_tokens * price.input_price
        + output_tokens * price.output_price
    ) / 1_000_000

    return cost_per_request * requests_per_day * days


if __name__ == "__main__":
    cost = estimate_monthly_cost("Claude Sonnet 5.5", 1000, 800, 300)
    print(f"Monthly cost: ${cost:.2f}")
