# Token Cost Estimator

Estimate and compare monthly API costs for cloud and on-prem LLMs, to support model selection.

## Why

Choosing an LLM is a trade-off between quality and cost. This tool turns expected usage into a monthly cost, so models can be compared on the same basis.


## Pricing data

Model prices are listed in [docs/model-pricing.md](docs/model-pricing.md).

## Roadmap

- [x] Pricing table
- [ ] Cost estimator in Python
- [ ] Command-line tool
- [ ] REST API with FastAPI
- [ ] Docker image and CI

## Usage (planned)

```bash
python estimator.py --model "Claude Sonnet 5.5" --requests 1000 --input-tokens 800 --output-tokens 300
```
