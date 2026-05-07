#!/usr/bin/env python3
"""Demo 数据 seed 脚本。

- 创建（或复用）一个 demo 账号
- 创建 3 个示例会话，每个塞几条 user 消息
- 不调 LLM、不调 ASR —— 演示时由演示者手动点"生成"，避免 seed 时烧 token

跑法：
    cd backend
    uv run python ../scripts/seed-demo.py
    BASE_URL=http://127.0.0.1:8002/api/v1 uv run python ../scripts/seed-demo.py

输出：demo 入口、账号、密码、3 个会话 ID。
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_BASE = "http://127.0.0.1:8000/api/v1"
EMAIL = "demo@aiken.dev"
PASSWORD = "demo-password-1"
NICKNAME = "Demo"

SAMPLES: list[dict[str, object]] = [
    {
        "title": "评测 Step-2 长文本",
        "messages": [
            "今天我们要写一篇关于阶跃星辰 Step-2 模型的评测文章",
            "重点讲它在 16K 上下文上的长文本理解能力，以及和 Claude、GPT-4 的对比",
            "结尾给一线开发者一个上手建议，包括 API 价格和接入难度",
        ],
    },
    {
        "title": "周末读书心得：纳瓦尔宝典",
        "messages": [
            "上周末读了《纳瓦尔宝典》",
            "印象最深的是关于杠杆的那一章：劳动力、资本、代码和媒体",
            "我想结合自己做产品的经历讲一讲这四种杠杆怎么组合",
            "适合公众号这种慢节奏阅读，目标是给同样在做副业的朋友一些启发",
        ],
    },
    {
        "title": "产品上线复盘：一次乌龙",
        "messages": [
            "我们的新功能昨天上线了",
            "前两个小时埋点数据看起来不太对，DAU 突然下滑 20%，我以为出大事了",
            "排查了两小时，最后发现是 BI 看板的口径错了，不是产品本身的问题",
            "今天复盘一下这次乌龙的根因和后续怎么避免，重点讲数据可信度建设",
        ],
    },
]


def _request(
    method: str,
    url: str,
    *,
    body: dict | None = None,
    token: str | None = None,
) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8") or "{}"
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        raise SystemExit(
            f"HTTP {e.code} on {method} {url}: {e.read().decode('utf-8', errors='replace')[:200]}"
        ) from e


def ensure_account(base: str) -> str:
    """注册或登录 demo 账号，返回 token。"""
    try:
        body = _request(
            "POST",
            f"{base}/auth/register",
            body={"email": EMAIL, "password": PASSWORD, "nickname": NICKNAME},
        )
        print(f"[seed] 注册新 demo 账号 {EMAIL}")
        return str(body["access_token"])
    except SystemExit as e:
        if "409" in str(e):
            body = _request(
                "POST",
                f"{base}/auth/login",
                body={"email": EMAIL, "password": PASSWORD},
            )
            print(f"[seed] 复用已有 demo 账号 {EMAIL}")
            return str(body["access_token"])
        raise


def existing_titles(base: str, token: str) -> set[str]:
    body = _request("GET", f"{base}/conversations?limit=200", token=token)
    return {(c.get("title") or "") for c in body.get("items", [])}


def seed_conversations(base: str, token: str) -> list[dict[str, str]]:
    have = existing_titles(base, token)
    created: list[dict[str, str]] = []
    for s in SAMPLES:
        if s["title"] in have:
            print(f"[seed] 跳过已存在：{s['title']}")
            continue
        conv = _request(
            "POST",
            f"{base}/conversations",
            body={"title": s["title"], "mode": "dialogue"},
            token=token,
        )
        cid = conv["id"]
        for content in s["messages"]:  # type: ignore[union-attr]
            _request(
                "POST",
                f"{base}/conversations/{cid}/messages",
                body={"role": "user", "content": content},
                token=token,
            )
        created.append({"title": str(s["title"]), "id": cid})
        print(f"[seed] 已创建会话 {cid} · {s['title']}")
    return created


def main() -> int:
    base = os.environ.get("BASE_URL", DEFAULT_BASE).rstrip("/")
    frontend = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    print(f"== Seeding demo data against {base} ==")
    token = ensure_account(base)
    created = seed_conversations(base, token)

    print()
    print("============================================================")
    print(" Demo 就绪")
    print("============================================================")
    print(f"  入口:    {frontend}/")
    print(f"  账号:    {EMAIL}")
    print(f"  密码:    {PASSWORD}")
    print(f"  本轮新建会话数: {len(created)}")
    if created:
        for c in created:
            print(f"    - {c['title']}  ({c['id']})")
    print()
    print(' 下一步：浏览器登录 → 进 "对话创作" → 选一个会话 → 点 "生成草稿"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
