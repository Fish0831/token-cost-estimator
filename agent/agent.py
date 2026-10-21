import sys

from dotenv import load_dotenv
import anthropic

from tools import TOOLS, run_tool

load_dotenv()
client = anthropic.Anthropic()

MODEL = "claude-haiku-5-5"
MAX_TURNS = 10  # 安全上限：最多跑 10 輪，避免無限迴圈

SYSTEM_PROMPT = (
    "你是 LLM API 成本顧問，用繁體中文回答。"
    "需要計算費用時，一定要使用工具，不要自己心算。"
    "如果使用者沒有提供必要的用量資訊，先問清楚再計算。"
)


def run_agent(messages: list) -> str:
    """執行 agent loop。messages 是整段對話紀錄，會直接被更新。"""
    total_in = total_out = 0

    for turn in range(1, MAX_TURNS + 1):
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        total_in += response.usage.input_tokens
        total_out += response.usage.output_tokens

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            answer = "".join(b.text for b in response.content if b.type == "text")
            print(f"\n[共 {turn} 輪，輸入 {total_in} token，輸出 {total_out} token]")
            return answer

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"[第 {turn} 輪] 呼叫工具 {block.name}，參數 {block.input}")
                result = run_tool(block.name, block.input)
                print(f"           結果：{result}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                    "is_error": result.startswith("錯誤"),
                })

        messages.append({"role": "user", "content": tool_results})

    return "超過最大輪數，Agent 停止。"


if __name__ == "__main__":
    # 單次模式：問題寫在指令後面
    if len(sys.argv) > 1:
        print("\n" + run_agent([{"role": "user", "content": sys.argv[1]}]))
        sys.exit()

    # 對話模式：保留 messages，可以一直追問
    messages = []
    print("成本估算 Agent（輸入 exit 離開）")
    while True:
        question = input("\n你：").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue
        messages.append({"role": "user", "content": question})
        print("\nAgent：" + run_agent(messages))
