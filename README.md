# Token Cost Estimator

Estimate and compare monthly LLM costs across cloud APIs and on-prem models, to support model selection and budgeting.

## Why

Choosing an LLM is a trade-off between quality and cost. This tool turns expected usage into a monthly cost, so models can be compared on the same basis.


## Pricing data

Model prices are listed in [docs/model-pricing.md](docs/model-pricing.md).

## Roadmap

- [x] Pricing table
- [x] Cost estimator in Python
- [x] Command-line tool
- [ ] REST API with FastAPI
- [ ] Docker image and CI

## Usage

Requires Python 3.9+.

Estimate one model:

```bash
python cli.py --model "Claude Sonnet 5.5" --requests 1000 --input 800 --output 300
```

```
Claude Sonnet 5.5: $138.00 / month
```

Compare all models (omit `--model`):

```bash
python cli.py --requests 1000 --input 800 --output 300
```

```
Claude Haiku 5.5     $    6.90
GPT-5.6 Luna         $   15.60
Gemini 3.8 Flash     $   51.75
Claude Sonnet 5.5    $  138.00
GPT-5.6 Terra        $  156.00
```

| Option | Meaning | Default |
| --- | --- | --- |
| `--model` | Model name in `data/models.json`; omit to compare all | — |
| `--requests` | Requests per day | required |
| `--input` | Input tokens per request | required |
| `--output` | Output tokens per request | required |
| `--days` | Days per month | 30 |

Run tests:

```bash
pip install pytest
python -m pytest -v
```

## Design

### Inputs

| Field | Description | Example |
| --- | --- | --- |
| `model` | Model name from the pricing table | Claude Sonnet 5.5 |
| `requests_per_day` | API calls per day | 1000 |
| `input_tokens` | Average input tokens per request | 800 |
| `output_tokens` | Average output tokens per request | 300 |
| `days` | Days per month (default 30) | 30 |

### Outputs

- Cost per request (USD)
- Monthly input cost, output cost, and total (USD)

### Formula

```
cost_per_request = (input_tokens × input_price + output_tokens × output_price) / 1,000,000
monthly_cost     = cost_per_request × requests_per_day × days
```

Prices are in USD per 1M tokens, from [docs/model-pricing.md](docs/model-pricing.md).

### Example

Claude Sonnet 5.5 ($2.00 input, $10.00 output), 1,000 requests per day, 800 input and 300 output tokens:

- Input: 800 × 1,000 × 30 = 24M tokens × $2.00 = $48.00
- Output: 300 × 1,000 × 30 = 9M tokens × $10.00 = $90.00
- Total: $138.00 per month

### Out of scope for v1

- On-prem models, whose cost depends on hardware rather than tokens
- Long-context price tiers, batch discounts, and prompt caching
