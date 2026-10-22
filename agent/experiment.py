"""比較實驗：同一組題目分別給單一 Agent 和多代理人回答，記錄 token、費用、時間與答案。

執行方式：
    python agent/experiment.py          # 跑全部 6 題
    python agent/experiment.py 1 6      # 只跑第 1 題和第 6 題
結果存在 reports/experiment_時間.csv（reports/ 已被 .gitignore 忽略）。
"""
import csv
import sys
import time
from collections import Counter
from datetime import datetime

from rich.markup import escape
from rich.table import Table

import multi_agent
import tools
from agent import new_total, run_agent
from tools import PROJECT_ROOT, run_tool
from ui import console, shorten

REPORT_DIR = PROJECT_ROOT / "reports"
MODES = ["單一Agent", "多代理人"]

USAGE = "每天 1000 次請求，每次輸入 800 token、輸出 300 token。"

QUESTIONS = [
    {
        "id": 1,
        "kind": "資訊完整",
        "question": USAGE + "用 Claude Sonnet 5.5 一個月要多少錢？",
        "expected": "$138.00",
    },
    {
        "id": 2,
        "kind": "兩模型差額",
        "question": USAGE + "Claude Sonnet 5.5 和 Claude Haiku 5.5 一個月差多少錢？一年差多少？",
        "expected": "月差 $131.10、年差 $1,573.20",
    },
    {
        "id": 3,
        "kind": "比較所有模型",
        "question": USAGE + "比較所有模型一個月的費用，哪個最便宜、哪個最貴？",
        "expected": "最便宜 Claude Haiku 5.5 $6.90；最貴 GPT-5.6 Terra $156.00"
                    "（Luna $15.60、Gemini $51.75、Sonnet $138.00）",
    },
    {
        "id": 4,
        "kind": "缺用量資訊",
        "question": "我們想做一個客服機器人，用哪個模型最省錢？",
        "expected": "反問用量；或直接說 Haiku 5.5 輸入輸出單價都最低。不能自己編用量算出金額",
    },
    {
        "id": 5,
        "kind": "不存在的模型",
        "question": USAGE + "用 GPT-6 Ultra 一個月要多少錢？",
        "expected": "說明沒有這個模型並列出可用模型，不能自己編單價",
    },
    {
        "id": 6,
        "kind": "九月用量分析",
        "question": "幫我看九月的用量紀錄，有沒有異常？如果全部改用 Claude Haiku 5.5，一個月能省多少？",
        "expected": "異常：9/15–17 請求暴增、9/21–25 輸入變長；"
                    "Sonnet 約 $171.05、Haiku 約 $8.55、月省約 $162.50（差 0.1% 內算對）",
    },
]

FIELDS = [
    "id", "kind", "mode", "question", "expected",
    "input_tokens", "output_tokens", "cost_usd", "seconds",
    "tool_calls", "tool_detail", "delegations", "answer", "correct",
]

# ---------- 量測用的替換（monkeypatch）：只在這個實驗裡生效，不改原本的檔案 ----------

tool_counter = Counter()  # 每次執行前清空，記錄這次呼叫了哪些工具、各幾次


def counting_run_tool(name: str, args: dict) -> str:
    """先記一筆，再交給原本的 run_tool 執行。"""
    tool_counter[name] += 1
    return run_tool(name, args)


_original_run_agent = multi_agent.run_agent


def counting_run_agent(*args, **kwargs):
    """主管每委派一次，就會啟動一次估算 Agent；在這裡記錄委派次數。"""
    if kwargs.get("name") == "估算Agent":
        tool_counter["ask_cost_estimator"] += 1
    return _original_run_agent(*args, **kwargs)


class AutoReject:
    """取代 save_report 裡的確認框：實驗不需要存檔，一律回答「否」，不用守在電腦前。"""

    @staticmethod
    def ask(*args, **kwargs) -> bool:
        console.print("[magenta]（實驗模式：自動拒絕寫入檔案）[/]")
        return False


def install_patches() -> None:
    multi_agent.run_tool = counting_run_tool
    multi_agent.run_agent = counting_run_agent
    tools.Confirm = AutoReject


# ---------- 實驗本體 ----------

def run_one(mode: str, q: dict) -> dict:
    """用指定的模式回答一題。每次都是全新對話，避免前一題的記憶影響結果。"""
    tool_counter.clear()
    total = new_total()
    messages = [{"role": "user", "content": q["question"]}]
    start = time.perf_counter()
    try:
        if mode == "單一Agent":
            answer = run_agent(messages, tool_runner=counting_run_tool, name="單一Agent", total=total)
        else:
            answer = multi_agent.run_multi_agent(messages, total)
    except Exception as e:
        answer = f"錯誤：執行失敗：{e}"
    seconds = round(time.perf_counter() - start, 2)

    real_tools = {k: v for k, v in tool_counter.items() if k != "ask_cost_estimator"}
    detail = ", ".join(f"{k}×{v}" for k, v in sorted(real_tools.items())) or "（無）"
    return {
        "id": q["id"],
        "kind": q["kind"],
        "mode": mode,
        "question": q["question"],
        "expected": q["expected"],
        "input_tokens": total["input_tokens"],
        "output_tokens": total["output_tokens"],
        "cost_usd": round(total["cost_usd"], 6),
        "seconds": seconds,
        "tool_calls": sum(real_tools.values()),
        "tool_detail": detail,
        "delegations": tool_counter["ask_cost_estimator"],
        "answer": answer,
        "correct": "",  # 由 F1sh 對照 expected 人工填寫
    }


def show_summary(rows: list) -> None:
    """印出每一次執行的數字，以及兩種模式的合計和倍數。"""
    table = Table(title="比較實驗結果")
    for col in ["題", "類型", "模式", "輸入", "輸出", "費用", "秒數", "工具", "委派"]:
        table.add_column(col)
    for r in rows:
        table.add_row(
            str(r["id"]), r["kind"], r["mode"],
            str(r["input_tokens"]), str(r["output_tokens"]),
            f"${r['cost_usd']:.4f}", str(r["seconds"]),
            str(r["tool_calls"]), str(r["delegations"]),
        )
    console.print(table)

    sums = {}
    for mode in MODES:
        mode_rows = [r for r in rows if r["mode"] == mode]
        sums[mode] = {
            key: sum(r[key] for r in mode_rows)
            for key in ("input_tokens", "output_tokens", "cost_usd", "seconds", "tool_calls")
        }
        s = sums[mode]
        console.print(
            f"[bold]{mode} 合計[/]：輸入 {s['input_tokens']} · 輸出 {s['output_tokens']} token · "
            f"${s['cost_usd']:.4f} · {s['seconds']:.1f} 秒 · 工具 {s['tool_calls']} 次"
        )

    single, multi = sums["單一Agent"], sums["多代理人"]
    if all(single[k] > 0 for k in ("input_tokens", "output_tokens", "cost_usd", "seconds")):
        console.print(
            f"[bold cyan]多代理人 ÷ 單一Agent[/]：輸入 {multi['input_tokens'] / single['input_tokens']:.1f} 倍 · "
            f"輸出 {multi['output_tokens'] / single['output_tokens']:.1f} 倍 · "
            f"費用 {multi['cost_usd'] / single['cost_usd']:.1f} 倍 · "
            f"時間 {multi['seconds'] / single['seconds']:.1f} 倍"
        )


def main() -> None:
    selected = {int(x) for x in sys.argv[1:]}
    questions = [q for q in QUESTIONS if not selected or q["id"] in selected]

    install_patches()
    REPORT_DIR.mkdir(exist_ok=True)
    path = REPORT_DIR / f"experiment_{datetime.now():%Y%m%d_%H%M%S}.csv"

    rows = []
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for q in questions:
            for mode in MODES:
                console.rule(f"[bold]Q{q['id']} {q['kind']} · {mode}")
                row = run_one(mode, q)
                rows.append(row)
                writer.writerow(row)
                f.flush()  # 每跑完一次就寫進檔案，中途中斷也保得住前面的結果
                console.print(f"[green]答案：[/]{escape(shorten(row['answer'], 200))}")

    show_summary(rows)
    console.print(f"\n[bold]CSV 已存到 {path.relative_to(PROJECT_ROOT)}[/]")


if __name__ == "__main__":
    main()
