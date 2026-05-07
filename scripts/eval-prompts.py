#!/usr/bin/env python3
"""Prompt 评测：用固定的样本跑 step-2-16k，记录字数 / 段落数 / 标题长 / 耗时。

不放在 pytest 里（每次跑都消耗 token）。手动执行：

    cd backend
    uv run python ../scripts/eval-prompts.py
    uv run python ../scripts/eval-prompts.py --sample 1   # 只跑第 1 个样本
    uv run python ../scripts/eval-prompts.py --tone 正式  # 单独看一个风格

输出 docs/prompt-eval-<timestamp>.md，方便对照前后版本。
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

# 让脚本能 from app.* import
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import settings  # noqa: E402
from app.services.llm import StepLLMClient  # noqa: E402
from app.services.prompts import (  # noqa: E402
    Length,
    Tone,
    build_dialogue_generation_messages,
    split_title_and_body,
)


SAMPLES: list[dict[str, object]] = [
    {
        "name": "S1 阶跃 Step-2 评测",
        "messages": [
            "今天我们要写一篇关于阶跃星辰 Step-2 模型的评测",
            "重点讲长文本理解能力，对比 Claude 和 GPT-4",
            "结尾给开发者一个上手建议",
        ],
    },
    {
        "name": "S2 周末读书心得",
        "messages": [
            "上周末读了《纳瓦尔宝典》",
            "印象最深的是关于杠杆的那一章：劳动力、资本、代码和媒体",
            "我想结合自己做产品的经历讲一讲",
            "适合公众号这种慢节奏阅读",
        ],
    },
    {
        "name": "S3 公司产品上线复盘",
        "messages": [
            "我们的新功能昨天上线了",
            "前两个小时埋点数据看起来不太对，我以为出大事了",
            "后来发现是 BI 看板的口径错了，不是产品本身的问题",
            "今天复盘一下这次乌龙的根因和后续怎么避免",
        ],
    },
    {
        "name": "S4 极短输入（鲁棒性）",
        "messages": ["今天天气不错"],
    },
    {
        "name": "S5 散乱口语",
        "messages": [
            "嗯就是那个 我想说一下",
            "其实我觉得吧 这个事情",
            "你们看 现在大家都在卷模型",
            "但其实呢应用层才是机会",
            "不知道你们怎么看",
        ],
    },
]


def fmt_md_table(rows: Sequence[dict[str, object]]) -> str:
    """把字典数组渲染成 markdown 表，列顺序按第一行的 key。"""
    if not rows:
        return ""
    cols = list(rows[0].keys())
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
    return "\n".join(lines)


async def run_one(
    client: StepLLMClient,
    *,
    sample_name: str,
    user_messages: list[str],
    tone: Tone,
    length: Length,
) -> dict[str, object]:
    msgs = build_dialogue_generation_messages(
        user_messages=user_messages, tone=tone, length=length
    )
    t0 = time.monotonic()
    raw = await client.complete(msgs, temperature=0.7)
    elapsed = time.monotonic() - t0

    title, body = split_title_and_body(raw)
    paragraphs = [p for p in body.split("\n\n") if p.strip()]
    h2 = body.count("\n## ") + (1 if body.startswith("## ") else 0)

    return {
        "样本": sample_name,
        "tone": tone,
        "length": length,
        "总字数": len(raw),
        "正文字数": len(body),
        "段落数": len(paragraphs),
        "二级标题数": h2,
        "标题字数": len(title),
        "耗时(s)": f"{elapsed:.1f}",
        "_title": title,
        "_body_excerpt": body[:160].replace("\n", " "),
    }


async def amain(args: argparse.Namespace) -> int:
    if not settings.step_api_key:
        print("STEP_API_KEY 未配置，无法跑评测", file=sys.stderr)
        return 2

    client = StepLLMClient(
        api_key=settings.step_api_key,
        base_url=settings.step_api_base_url,
        model=settings.step_llm_model,
    )

    samples = SAMPLES
    if args.sample is not None:
        samples = [SAMPLES[args.sample - 1]]

    tones: list[Tone] = [args.tone] if args.tone else ["亲切", "正式"]
    lengths: list[Length] = [args.length] if args.length else ["short", "medium"]

    rows: list[dict[str, object]] = []
    for s in samples:
        for tone in tones:
            for length in lengths:
                print(f"→ {s['name']:30s} tone={tone:4s} length={length:6s} ...", end=" ", flush=True)
                row = await run_one(
                    client,
                    sample_name=str(s["name"]),
                    user_messages=list(s["messages"]),  # type: ignore[arg-type]
                    tone=tone,
                    length=length,
                )
                print(f"{row['总字数']} 字 / {row['耗时(s)']}s")
                rows.append(row)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = ROOT / "docs" / f"prompt-eval-{ts}.md"
    out_path.parent.mkdir(exist_ok=True)

    summary_rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    detail = "\n\n".join(
        f"### {r['样本']} · tone={r['tone']} · length={r['length']}\n\n"
        f"**标题**: {r['_title']}\n\n**正文开头**: {r['_body_excerpt']}…"
        for r in rows
    )

    out_path.write_text(
        f"# Prompt 评测 {ts}\n\nmodel: `{client.model}`\n\n## 摘要\n\n"
        f"{fmt_md_table(summary_rows)}\n\n## 详情\n\n{detail}\n",
        encoding="utf-8",
    )
    print(f"\n报告写入: {out_path}")
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Prompt 评测脚本")
    p.add_argument("--sample", type=int, choices=[1, 2, 3, 4, 5], help="只跑某个样本")
    p.add_argument("--tone", choices=["亲切", "正式", "幽默", "理性"])
    p.add_argument("--length", choices=["short", "medium", "long"])
    return p.parse_args()


if __name__ == "__main__":
    sys.exit(asyncio.run(amain(parse_args())))
