import sys

from rich.panel import Panel

from agent import new_total, run_agent, show_answer
from tools import TOOLS, run_tool
from ui import console

MANAGER_PROMPT = (
    "你是 LLM API 成本顧問團隊的主管，用繁體中文回答使用者。"
    "你不自己計算任何數字，所有計算都要用 ask_cost_estimator 交給估算 Agent。"
    "你的工作：1. 理解使用者的需求；如果缺少必要的用量資訊（每天請求次數、每次輸入與輸出 token），"
    "直接問使用者，不要交給估算 Agent。2. 把計算任務寫清楚，交給估算 Agent。"
    "3. 整合估算 Agent 的結果，用使用者看得懂的方式回答，並給出建議。"
)

ESTIMATOR_PROMPT = (
    "你是估算 Agent，只負責計算。你收到的任務來自主管，不是使用者。"
    "所有數字都要用工具計算，不要心算。每個數字只算一次，不要用不同算式重複驗算。"
    "如果任務缺少必要的數字，不要自己猜，直接回報缺少哪些資訊。"
    "回覆要簡潔，只列出計算結果和使用的假設。"
)

# 最小權限：估算 Agent 只拿得到計算用的工具，拿不到會改變外部狀態的 save_report
ESTIMATOR_TOOL_NAMES = {"list_models", "estimate_monthly_cost", "compare_models", "calculate", "read_usage_log"}
ESTIMATOR_TOOLS = [t for t in TOOLS if t["name"] in ESTIMATOR_TOOL_NAMES]


def estimator_tool_runner(name: str, args: dict) -> str:
    """估算 Agent 的工具執行函式：不在允許清單裡的工具，一律拒絕。"""
    if name not in ESTIMATOR_TOOL_NAMES:
        return f"錯誤：估算 Agent 沒有使用 {name} 的權限"
    return run_tool(name, args)


MANAGER_TOOLS = [
    {
        "name": "ask_cost_estimator",
        "description": (
            "把具體的計算任務交給估算 Agent。估算 Agent 可以查模型單價、估算單一模型的月費用、"
            "比較所有模型、做數學計算、讀取使用者九月的實際用量紀錄。"
            "估算 Agent 看不到你和使用者的對話，所以任務描述要完整，包含所有用量數字和要比較的模型。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "交給估算 Agent 的完整任務描述"},
            },
            "required": ["task"],
        },
    },
    # 存檔只有主管能做：主管能直接看到使用者有沒有要求存檔
    next(t for t in TOOLS if t["name"] == "save_report"),
]


def run_multi_agent(messages: list, total: dict | None = None) -> str:
    """執行主管 Agent。主管需要計算時，會呼叫估算 Agent。兩個 Agent 共用同一個累計表。"""
    if total is None:
        total = new_total()

    def manager_tool_runner(name: str, args: dict) -> str:
        if name == "save_report":
            return run_tool(name, args)
        if name != "ask_cost_estimator":
            return f"錯誤：沒有叫做 {name} 的工具"
        try:
            # 每次委派都開一段全新的對話：估算 Agent 只看得到主管寫的任務
            return run_agent(
                [{"role": "user", "content": args["task"]}],
                system_prompt=ESTIMATOR_PROMPT,
                tools=ESTIMATOR_TOOLS,
                tool_runner=estimator_tool_runner,
                name="估算Agent",
                total=total,
            )
        except Exception as e:
            return f"錯誤：估算 Agent 執行失敗：{e}"

    return run_agent(
        messages,
        system_prompt=MANAGER_PROMPT,
        tools=MANAGER_TOOLS,
        tool_runner=manager_tool_runner,
        name="主管Agent",
        total=total,
    )


def show_total(total: dict) -> None:
    console.print(
        f"[bold]整個任務合計：輸入 {total['input_tokens']} · 輸出 {total['output_tokens']} token · "
        f"${total['cost_usd']:.4f}[/]"
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        total = new_total()
        show_answer(run_multi_agent([{"role": "user", "content": sys.argv[1]}], total), title="主管Agent")
        show_total(total)
        sys.exit()

    messages = []
    console.print(Panel("多代理人成本顧問（輸入 exit 離開）", border_style="cyan"))
    while True:
        question = console.input("\n[bold cyan]你：[/]").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue
        messages.append({"role": "user", "content": question})
        total = new_total()
        show_answer(run_multi_agent(messages, total), title="主管Agent")
        show_total(total)
