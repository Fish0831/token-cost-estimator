# Model Pricing

Standard API prices in USD per 1M tokens, excluding batch and caching discounts.
On-prem models have no API price; their cost is GPU hardware and power.
Checked: 2026-10-08.

| Model | Vendor | Tier | Input | Output | Notes |
| --- | --- | --- | --- | --- | --- |
| GPT-5.6 Sol | OpenAI | Flagship | 5.00 | 30.00 | Price for context under 270K |
| GPT-5.6 Terra | OpenAI | Mid | 2.00 | 12.00 | Price for context under 270K |
| GPT-5.6 Luna | OpenAI | Small | 0.20 | 1.20 | Price for context under 270K |
| Claude Opus 5.5 | Anthropic | Flagship | 4.00 | 20.00 | |
| Claude Sonnet 5.5 | Anthropic | Mid | 2.00 | 10.00 | |
| Claude Haiku 5.5 | Anthropic | Small | 0.10 | 0.50 | 0.50 / 2.50 for prompts over 100K |
| Gemini 3.1 Pro (preview) | Google | Flagship | 2.00 | 12.00 | 4.00 / 18.00 for prompts over 200K |
| Gemini 3.8 Flash | Google | Mid | 0.75 | 3.75 | Rises to 1.50 / 7.50 on 2027-01-01 |
| Gemini 3.1 Flash-Lite | Google | Small | 0.25 | 1.50 | |
| Gemma 4 E4B | Google | On-prem (edge) | - | - | 4.5B effective, 128K context, Apache 2.0 |
| Gemma 4 31B | Google | On-prem (workstation) | - | - | 30.7B, 256K context, Apache 2.0 |
| gpt-oss-120b | OpenAI | On-prem (server) | - | - | 117B total / 5.1B active, single 80GB GPU, Apache 2.0 |

## Sources

- OpenAI: https://openai.com/api/pricing/
- Anthropic: https://platform.claude.com/docs/en/about-claude/pricing
- Google: https://ai.google.dev/gemini-api/docs/pricing
- Gemma 4: https://ai.google.dev/gemma/docs/core/model_card_4
- gpt-oss: https://huggingface.co/openai/gpt-oss-120b
