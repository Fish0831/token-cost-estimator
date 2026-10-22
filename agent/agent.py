import json
import sys
import time
from datetime import datetime
from typing import Callable

from dotenv import load_dotenv
import anthropic
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel

# tools.py 會把專案根目錄加進 sys.path，所以要先 import tools，才能 import estimator
from tools import PROJECT_ROOT, TOOLS, run_tool
from estimator import load_models
from ui import console, shorten

load_dotenv()
client = anthropic.Anthropic()

MODEL = "claude-haiku-5-5"
MODEL_PRICE_NAME = "Claude Haiku 5.5"  # 在 models.json 裡的名稱，用來查單價
PRICE = load_models()[MODEL_PRICE_NAME]
MAX_TURNS = 10  # 安全上限：最多跑 10 輪，避免無限迴圈
MAX_TOKENS = 4096  # 每次回應最多輸出的 token 數
MAX_COST_USD = 0.50  # 費用上限：一次任務（包含所有 Agent）最多花多少美元
TRAJECTORY_DIR = PROJECT_ROOT / "trajectories"

SYSTEM_PROMPT = (
    "你是 LLM API 成本顧問，用繁體中文回答。"
    "需要計算費用時，一定要使用工具，不要自己心算。"
    "如果使用者沒有提供必要的用量資訊，先問清楚再計算。"
)


def new_total() -> dict:
    """建立一個空的累計表，多個 Agent 共用同一個，用來算整個任務的總用量。"""
    return {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}


def token_cost(input_tokens: int, output_tokens: int) -> float:
    """根據 models.json 的單價（每百萬 token），算出這次呼叫花了多少美元。"""
    return (input_tokens * PRICE.input_price + output_tokens * PRICE.output_price) / 1_000_000


def to_jsonable(obj):
    """把 SDK 回傳的物件（例如 tool_use 區塊）轉成可以存成 JSON 的 dict。"""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, list):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    return obj


def save_trajectory(name: str, system_prompt: str, messages: list, stats: dict, answer: str):
    """把這次執行的完整過程存成 JSON 檔，回傳檔案路徑。"""
    TRAJECTORY_DIR.mkdir(exist_ok=True)
    path = TRAJECTORY_DIR / f"{datetime.now():%Y%m%d_%H%M%S_%f}_{name}.json"
    data = {
        "agent": name,
        "model": MODEL,
        "system_prompt": system_prompt,
        "stats": stats,
        "answer": answer,
        "messages": to_jsonable(messages),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_agent(
    messages: list,
    system_prompt: str = SYSTEM_PROMPT,
    tools: list = TOOLS,
    tool_runner: Callable[[str, dict], str] = run_tool,
    name: str = "Agent",
    total: dict | None = None,
    max_cost: float = MAX_COST_USD,
) -> str:
    """執行 agent loop，回傳最後的答案。

    messages：整段對話紀錄，會直接被更新
    system_prompt / tools / tool_runner：這個 Agent 的角色、可用工具、執行工具的函式
    name：畫面上和執行軌跡檔名中顯示的 Agent 名稱
    total：多個 Agent 共用的累計表（new_total() 建立），用來算整個任務的總用量和費用上限
    max_cost：整個任務的費用上限（美元）
    """
    if total is None:
        total = new_total()
    stats = {"turns": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
    start = time.perf_counter()

    def finish(answer: str) -> str:
        """所有結束的情況都經過這裡：記錄時間、存執行軌跡、印出統計。"""
        stats["seconds"] = round(time.perf_counter() - start, 2)
        stats["cost_usd"] = round(stats["cost_usd"], 6)
        path = save_trajectory(name, system_prompt, messages, stats, answer)
        console.print(
            f"[dim]{name}：{stats['turns']} 輪 · 輸入 {stats['input_tokens']} · "
            f"輸出 {stats['output_tokens']} token · ${stats['cost_usd']:.4f} · "
            f"{stats['seconds']} 秒 · 軌跡 {path.name}[/]"
        )
        return answer

    for turn in range(1, MAX_TURNS + 1):
        # 只有等待 API 時顯示轉圈動畫；工具執行（可能要 y/n 確認）不包在裡面
        with console.status(f"[cyan]{name} 思考中…"):
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                tools=tools,
                messages=messages,
            )

        used_in = response.usage.input_tokens
        used_out = response.usage.output_tokens
        cost = token_cost(used_in, used_out)
        stats["turns"] = turn
        stats["input_tokens"] += used_in
        stats["output_tokens"] += used_out
        stats["cost_usd"] += cost
        total["input_tokens"] += used_in
        total["output_tokens"] += used_out
        total["cost_usd"] += cost

        # 結束原因 1：回應被截斷。不把不完整的回應加進對話紀錄
        if response.stop_reason == "max_tokens":
            console.print(f"[red]{name} 第 {turn} 輪的回應超過 max_tokens（{MAX_TOKENS}），被截斷了[/]")
            return finish("錯誤：回應太長被截斷，沒有完成。請把問題拆小一點再問一次。")

        # 結束原因 2：模型不再呼叫工具，任務完成
        if response.stop_reason != "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            answer = "".join(b.text for b in response.content if b.type == "text")
            return finish(answer)

        # 結束原因 3：還想呼叫工具，但整個任務已經超過費用上限。同樣不加進對話紀錄
        if total["cost_usd"] > max_cost:
            console.print(
                f"[red]已花費 ${total['cost_usd']:.4f}，超過費用上限 ${max_cost}，{name} 停止[/]"
            )
            return finish(f"錯誤：已超過費用上限 ${max_cost}，Agent 停止。")

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                console.print(
                    f"[yellow]{name} 第 {turn} 輪[/] → 呼叫 [bold]{block.name}[/]  "
                    f"{escape(shorten(str(block.input)))}"
                )
                result = tool_runner(block.name, block.input)
                console.print(f"[dim]   結果：{escape(shorten(result, 300))}[/]")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                    "is_error": result.startswith("錯誤"),
                })

        messages.append({"role": "user", "content": tool_results})

    # 結束原因 4：跑滿 MAX_TURNS 輪還沒完成
    return finish("錯誤：超過最大輪數，Agent 停止。")


def show_answer(answer: str, title: str = "Agent") -> None:
    """把 Agent 的回答用 Markdown 渲染，放進綠色外框。"""
    console.print(Panel(Markdown(answer), title=title, border_style="green"))


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
