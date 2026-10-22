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
- [x] AI agent with tool use (hand-written loop, no framework)
- [ ] REST API with FastAPI
- [ ] Docker image and CI

## Usage

Requires Python 3.10+.

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

## AI Agent

A cost-advisor agent that answers questions in natural language (Traditional Chinese) by calling the estimator as tools. It runs on the Claude API (`claude-haiku-5-5`). The agent loop is written by hand with the `anthropic` SDK; no agent framework is used.

### Setup

```bash
pip install anthropic python-dotenv rich
```

Create a `.env` file in the project root (it is ignored by Git):

```
ANTHROPIC_API_KEY=your-api-key
```

### Run

Single agent, interactive (type `exit` to quit):

```bash
python agent/agent.py
```

Single agent, one question:

```bash
python agent/agent.py "每天 1000 次請求，每次輸入 800、輸出 300 token，Sonnet 5.5 和 Haiku 5.5 一個月差多少？"
```

Multi-agent (a manager agent delegates calculations to an estimator agent):

```bash
python agent/multi_agent.py
```

Compare single agent vs multi-agent on 6 test questions (results are saved to `reports/experiment_*.csv`):

```bash
python agent/experiment.py        # all questions
python agent/experiment.py 1 6    # only questions 1 and 6
```

### Tools

| Tool | What it does |
| --- | --- |
| `list_models` | List models and their input / output prices |
| `estimate_monthly_cost` | Monthly cost of one model for a given usage |
| `compare_models` | Monthly cost of all models, cheapest first |
| `calculate` | Evaluate `+ - * /` expressions safely (AST whitelist, no `eval`) |
| `read_usage_log` | Read daily usage from `data/sample_usage.csv` (the agent can only choose dates, not the file) |
| `save_report` | Save a Markdown report to `reports/`, after the user confirms |

Sample September usage data (with two planted anomalies) can be regenerated with `python agent/make_sample_usage.py`.

### Safety limits

- **Stop conditions**: the loop ends when the task is done, a response is truncated (`max_tokens`), the cost limit ($0.50 per task) is exceeded, or 10 turns are reached. Truncated or over-budget responses are not added to the conversation history.
- **Human in the loop**: `save_report` shows a preview and asks for confirmation; it keeps only the file name, so it cannot write outside `reports/`.
- **Least privilege**: in multi-agent mode, only the manager can save files. The estimator agent does not see `save_report`, and its tool calls are checked again at run time.
- **Trajectories**: every run is saved as JSON in `trajectories/` (messages, tokens, cost, seconds) for debugging.

### Single agent vs multi-agent

6 questions (complete info, two-model difference, compare all models, missing usage, unknown model, September usage analysis), one run each, `claude-haiku-5-5`:

| Mode | Input tokens | Output tokens | Cost | Time |
| --- | ---: | ---: | ---: | ---: |
| Single agent | 39,576 | 6,197 | $0.0071 | 39.8 s |
| Multi-agent | 69,693 | 16,114 | $0.0150 | 96.2 s |
| Ratio | 1.8× | 2.6× | 2.1× | 2.4× |

Findings:

- For short, well-defined cost questions, the multi-agent setup cost about twice as much and did not improve accuracy.
- Extra tokens came from re-checking results with repeated `calculate` calls, and from the estimator writing a full report that the manager then rewrote.
- In one question the estimator agent assumed 365 days per year while months used 30 days, because the manager's task did not say how to count a year. Hand-offs can lose assumptions.
- Both modes named the wrong weekdays for the September anomalies: there is no calendar tool, so the model guessed.

### Files

| File | Purpose |
| --- | --- |
| `agent/agent.py` | Agent loop (`run_agent`), cost tracking, trajectories |
| `agent/tools.py` | Tool definitions (`TOOLS`) and dispatcher (`run_tool`) |
| `agent/multi_agent.py` | Manager + estimator agents |
| `agent/experiment.py` | Single vs multi-agent comparison |
| `agent/ui.py` | Shared `rich` console |
| `agent/hello_claude.py`, `agent/first_tool_call.py` | First API call and first tool call |

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
