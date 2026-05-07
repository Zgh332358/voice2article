"""prompts 工具的纯函数测试 —— 不调 LLM。"""

import pytest

from app.services.prompts import build_dialogue_generation_messages, split_title_and_body


def test_split_clean_title() -> None:
    title, body = split_title_and_body("Step-2 长文本评测\n\n## 引言\n这是正文。")
    assert title == "Step-2 长文本评测"
    assert body.startswith("## 引言")


def test_split_strips_hash_and_bold_and_quotes() -> None:
    title, body = split_title_and_body("# **《Step-2 评测》**\n\n正文。")
    assert title == "Step-2 评测"
    assert body == "正文。"


def test_split_falls_back_when_first_line_looks_like_body() -> None:
    raw = "今天天气不错，阳光真好。\n\n这只是一段开篇。"
    title, body = split_title_and_body(raw)
    assert title == ""
    assert body == raw.strip()


def test_split_handles_empty() -> None:
    assert split_title_and_body("") == ("", "")


def test_split_too_long_title_treated_as_body() -> None:
    long_first = "x" * 60
    title, body = split_title_and_body(f"{long_first}\n\n正文")
    assert title == ""
    assert long_first in body


def test_build_messages_rejects_empty() -> None:
    with pytest.raises(ValueError, match="user_messages"):
        build_dialogue_generation_messages(user_messages=[])


def test_build_messages_includes_user_lines_and_tone() -> None:
    msgs = build_dialogue_generation_messages(
        user_messages=["想法 A", "想法 B"],
        tone="正式",
        length="short",
    )
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"
    user_content = msgs[1]["content"]
    assert "想法 A" in user_content
    assert "想法 B" in user_content
    assert "正式" in user_content
    assert "600-1000" in user_content


def test_build_messages_extra_instructions_appended() -> None:
    msgs = build_dialogue_generation_messages(
        user_messages=["x"],
        extra_instructions="请避免使用专业术语",
    )
    assert "避免使用专业术语" in msgs[1]["content"]
