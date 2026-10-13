import json
from pathlib import Path

MODELS_PATH = Path(__file__).parent / "data" / "models.json"


def load_models():
    with open(MODELS_PATH, encoding="utf-8") as f:
        return json.load(f)


def estimate_monthly_cost(model, requests_per_day, input_tokens, output_tokens, days=30):
    models = load_models()
    prices = models[model]

    cost_per_request = (
        input_tokens * prices["input_price"]
        + output_tokens * prices["output_price"]
    ) / 1_000_000

    return cost_per_request * requests_per_day * days


if __name__ == "__main__":
    cost = estimate_monthly_cost("Claude Sonnet 5.5", 1000, 800, 300)
    print(f"Monthly cost: ${cost:.2f}")
