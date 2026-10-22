import csv
import random
from datetime import date, timedelta
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "sample_usage.csv"
MODEL = "Claude Sonnet 5.5"

random.seed(42)  # 固定亂數種子，每次產生的資料都一樣

rows = []
start = date(2026, 9, 1)
for i in range(30):
    day = start + timedelta(days=i)

    # 平日的正常用量
    requests = random.randint(900, 1100)
    input_tokens = random.randint(750, 850)
    output_tokens = random.randint(280, 320)

    # 週末流量較低
    if day.weekday() >= 5:
        requests = random.randint(300, 400)

    # 9/15–9/17 行銷活動，流量暴增
    if date(2026, 9, 15) <= day <= date(2026, 9, 17):
        requests = random.randint(3800, 4200)

    # 9/21–9/25 上線長文件摘要功能，每次輸入變長
    if date(2026, 9, 21) <= day <= date(2026, 9, 25):
        input_tokens = random.randint(2300, 2500)

    rows.append({
        "date": day.isoformat(),
        "model": MODEL,
        "requests": requests,
        "avg_input_tokens": input_tokens,
        "avg_output_tokens": output_tokens,
    })

OUTPUT.parent.mkdir(exist_ok=True)
with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"已產生 {len(rows)} 天的資料：{OUTPUT}")
