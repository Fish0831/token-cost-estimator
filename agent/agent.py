import sys

from dotenv import load_dotenv
import anthropic
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel

from tools import TOOLS, run_tool
from ui import console, shorten

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
        # 只有等待 API 時顯示轉圈動畫；工具執行（可能要 y/n 確認）不包在裡面
        with console.status("[cyan]Agent 思考中…"):
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
            console.print(
                f"[dim]共 {turn} 輪 · 輸入 {total_in} token · 輸出 {total_out} token[/]"
            )
            return answer

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                console.print(
                    f"[yellow]第 {turn} 輪[/] → 呼叫 [bold]{block.name}[/]  "
                    f"{escape(shorten(str(block.input)))}"
                )
                result = run_tool(block.name, block.input)
                console.print(f"[dim]   結果：{escape(shorten(result, 300))}[/]")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                    "is_error": result.startswith("錯誤"),
                })

        messages.append({"role": "user", "content": tool_results})

    return "超過最大輪數，Agent 停止。"


def show_answer(answer: str) -> None:
    """把 Agent 的回答用 Markdown 渲染，放進綠色外框。"""
    console.print(Panel(Markdown(answer), title="Agent", border_style="green"))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        show_answer(run_agent([{"role": "user", "content": sys.argv[1]}]))
        sys.exit()

    messages = []
    console.print(Panel("成本估算 Agent（輸入 exit 離開）", border_style="cyan"))
    while True:
        question = console.input("\n[bold cyan]你：[/]").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue
        messages.append({"role": "user", "content": question})
        show_answer(run_agent(messages))
