from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic()

# 工具描述：告訴 Claude 有這個工具可以用
tools = [
    {
        "name": "estimate_monthly_cost",
        "description": "估算使用某個 LLM 模型一個月的 API 費用（美元）。當使用者詢問模型的使用成本時使用。",
        "input_schema": {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "description": "模型名稱，例如 Claude Sonnet 5.5、GPT-5.6 Terra",
                },
                "requests_per_day": {
                    "type": "integer",
                    "description": "每天的請求次數",
                },
                "input_tokens": {
                    "type": "integer",
                    "description": "每次請求平均的輸入 token 數",
                },
                "output_tokens": {
                    "type": "integer",
                    "description": "每次請求平均的輸出 token 數",
                },
            },
            "required": ["model", "requests_per_day", "input_tokens", "output_tokens"],
        },
    }
]

message = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=1000,
    tools=tools,
    messages=[
        {
            "role": "user",
            "content": "我每天要用 Claude Sonnet 5.5 處理 1000 次請求，每次輸入 800 token、輸出 300 token，一個月要多少錢？",
        }
    ],
)

print("stop_reason:", message.stop_reason)
print()
for block in message.content:
    print("區塊類型:", block.type)
    if block.type == "text":
        print("  文字:", block.text)
    elif block.type == "tool_use":
        print("  工具名稱:", block.name)
        print("  參數:", block.input)
        print("  呼叫編號:", block.id)
    print()
