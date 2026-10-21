import sys
from pathlib import Path

# 讓 Python 找得到專案根目錄的 estimator.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from estimator import estimate_monthly_cost, load_models

MODEL_NAMES = list(load_models().keys())

TOOLS = [
    {
        "name": "estimate_monthly_cost",
        "description": (
            "估算使用某個 LLM 模型的 API 月費用（美元）。"
            "當使用者詢問某個模型在特定用量下要花多少錢時使用。"
            f"可用的模型名稱只有：{', '.join(MODEL_NAMES)}。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "description": "模型名稱，必須是可用模型名稱之一"},
                "requests_per_day": {"type": "integer", "description": "每天的請求次數"},
                "input_tokens": {"type": "integer", "description": "每次請求平均輸入 token 數"},
                "output_tokens": {"type": "integer", "description": "每次請求平均輸出 token 數"},
                "days": {"type": "integer", "description": "計算天數，預設 30"},
            },
            "required": ["model", "requests_per_day", "input_tokens", "output_tokens"],
        },
    }
]


def run_tool(name: str, args: dict) -> str:
    """執行 Claude 指定的工具，回傳結果文字。出錯時回傳錯誤訊息，讓 Claude 自己處理。"""
    try:
        if name == "estimate_monthly_cost":
            cost = estimate_monthly_cost(**args)
            return f"計算結果（美元）：{cost}"
        return f"錯誤：沒有叫做 {name} 的工具"
    except Exception as e:
        return f"錯誤：{e}"
