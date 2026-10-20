from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=500,
    messages=[
        {"role": "user", "content": "用一句話說明什麼是 AI Agent"}
    ],
)

for block in message.content:
    if block.type == "text":
        print(block.text)

print("輸入 token:", message.usage.input_tokens)
print("輸出 token:", message.usage.output_tokens)
