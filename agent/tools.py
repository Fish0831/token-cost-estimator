import ast
import operator
import sys
from pathlib import Path

from rich.markup import escape
from rich.panel import Panel
from rich.prompt import Confirm

from ui import console

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from estimator import compare_models, estimate_monthly_cost, load_models

MODEL_NAMES = list(load_models().keys())
REPORT_DIR = PROJECT_ROOT / "reports"

USAGE_PROPERTIES = {
    "requests_per_day": {"type": "integer", "description": "每天的請求次數"},
    "input_tokens": {"type": "integer", "description": "每次請求平均輸入 token 數"},
    "output_tokens": {"type": "integer", "description": "每次請求平均輸出 token 數"},
    "days": {"type": "integer", "description": "計算天數，預設 30"},
}
USAGE_REQUIRED = ["requests_per_day", "input_tokens", "output_tokens"]

TOOLS = [
    {
        "name": "list_models",
        "description": "列出所有可用的模型，以及每個模型的輸入、輸出單價（美元 / 每百萬 token）。當使用者想知道有哪些模型可選，或詢問單價時使用。",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "estimate_monthly_cost",
        "description": f"估算『單一』模型在特定用量下的 API 月費用（美元）。可用的模型名稱只有：{', '.join(MODEL_NAMES)}。",
        "input_schema": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "description": "模型名稱，必須是可用模型名稱之一"},
                **USAGE_PROPERTIES,
            },
            "required": ["model", *USAGE_REQUIRED],
        },
    },
    {
        "name": "compare_models",
        "description": "在同樣的用量下，計算『所有』模型的月費用，並由便宜到貴排序。當使用者想比較模型、找出最便宜的模型時使用。",
        "input_schema": {
            "type": "object",
            "properties": USAGE_PROPERTIES,
            "required": USAGE_REQUIRED,
        },
    },
    {
        "name": "calculate",
        "description": "計算數學算式，支援 + - * / 和括號。任何數字計算（兩個費用相減、倍數、百分比、換算成一年）都必須使用這個工具，不要自己心算。",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "要計算的算式，例如 (138 - 6.9) * 12"},
            },
            "required": ["expression"],
        },
    },
    {
        "name": "save_report",
        "description": "把整理好的內容存成 Markdown 報告檔（存在 reports 資料夾）。只有在使用者明確要求存檔或產出報告時才使用。執行前系統會先請使用者確認。",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "檔名，例如 cost_report.md"},
                "content": {"type": "string", "description": "報告的完整 Markdown 內容"},
            },
            "required": ["filename", "content"],
        },
    },
]

ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def calculate(expression: str) -> str:
    def evaluate(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPERATORS:
            return ALLOWED_OPERATORS[type(node.op)](evaluate(node.left), evaluate(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_OPERATORS:
            return ALLOWED_OPERATORS[type(node.op)](evaluate(node.operand))
        raise ValueError("只支援數字、+ - * / 和括號")

    value = evaluate(ast.parse(expression, mode="eval").body)
    return f"{expression} = {round(value, 4)}"


def save_report(filename: str, content: str) -> str:
    safe_name = Path(filename).name  # 只取檔名，防止寫到專案外
    if not safe_name.endswith(".md"):
        safe_name += ".md"
    path = REPORT_DIR / safe_name

    preview = content[:300] + ("……" if len(content) > 300 else "")
    console.print(
        Panel(
            escape(preview),
            title=f"Agent 想寫入 reports/{safe_name}",
            border_style="yellow",
        )
    )
    if not Confirm.ask("確定要寫入嗎？", console=console):
        return "錯誤：使用者拒絕寫入檔案"

    REPORT_DIR.mkdir(exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"已寫入 reports/{safe_name}"


def run_tool(name: str, args: dict) -> str:
    try:
        if name == "list_models":
            return "\n".join(
                f"{n}：輸入 ${p.input_price} / 輸出 ${p.output_price}（每百萬 token）"
                for n, p in load_models().items()
            )
        if name == "estimate_monthly_cost":
            return f"{args['model']} 月費用：${estimate_monthly_cost(**args):.2f}"
        if name == "compare_models":
            results = compare_models(**args)
            return "由便宜到貴：\n" + "\n".join(
                f"{i}. {n}：${c:.2f}" for i, (n, c) in enumerate(results, 1)
            )
        if name == "calculate":
            return calculate(**args)
        if name == "save_report":
            return save_report(**args)
        return f"錯誤：沒有叫做 {name} 的工具"
    except Exception as e:
        return f"錯誤：{e}"
