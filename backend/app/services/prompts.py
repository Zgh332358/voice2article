"""文章生成的 Prompt 模板。

只放文本，不调 LLM。每个函数返回一组 ChatMessage（system + user），
便于 generations.py 直接 plug 到 LLM client。
"""

from collections.abc import Sequence
from typing import Literal

from app.services.llm import ChatMessage

Tone = Literal["亲切", "正式", "幽默", "理性"]
Length = Literal["short", "medium", "long"]


_LENGTH_HINT: dict[Length, str] = {
    "short": "总字数 600-1000 字",
    "medium": "总字数 1500-2000 字",
    "long": "总字数 2500-3500 字",
}


SYSTEM_DIALOGUE_WRITER = """\
你是一位专业的微信公众号文章写作助手。
你的任务是把用户口述的零散想法，整理成一篇结构完整、可直接发布的公众号推文。

输出规范：
1. 第一行是文章标题（不要加书名号、不要加 # 号），紧凑、有钩子，不超过 30 字
2. 标题之后空一行，再开始正文
3. 正文用 Markdown：
   - 至少包含 引言、3-5 个主体段落、总结
   - 主体段落可使用 ## 二级标题
   - 适当使用列表、加粗、引用块
4. 不要返回 JSON、不要返回多余的 meta 信息，只输出标题 + 正文
5. 保持事实严谨：用户对话中没有提到的数据/事实不要编造
"""


def build_dialogue_generation_messages(
    *,
    user_messages: Sequence[str],
    tone: Tone = "亲切",
    length: Length = "medium",
    extra_instructions: str | None = None,
) -> list[ChatMessage]:
    """模式 A：纯对话生成。

    把用户在会话里说过的全部话拼成一个上下文块，引导 LLM 输出文章。
    """
    if not user_messages:
        raise ValueError("user_messages 不能为空")

    joined = "\n".join(f"- {m.strip()}" for m in user_messages if m.strip())
    extra = f"\n额外要求：\n{extra_instructions}" if extra_instructions else ""

    user_prompt = f"""\
以下是用户在一次语音对话中说的全部内容（按时间正序）：

{joined}

请把这些零散的想法整理成一篇微信公众号文章。

风格要求：
- 语气：{tone}（像{tone}的朋友在向读者讲述）
- 篇幅：{_LENGTH_HINT[length]}
- 结构：标题 + 引言 + 主体 + 总结
- 直接给出文章本身，不要附加"以下是文章"之类的客套话{extra}
"""

    return [
        ChatMessage("system", SYSTEM_DIALOGUE_WRITER),
        ChatMessage("user", user_prompt),
    ]


SYSTEM_TITLE_EXTRACTOR = """\
你是一位资深的微信公众号编辑。请阅读用户提供的文章正文，给出一个最适合的标题。

输出规范：
- 只输出标题本身一行，不超过 30 字
- 不要书名号、不要 # 号、不要任何前缀（如"标题："）
- 标题应当有钩子、有信息量
"""


def build_title_extraction_messages(article: str) -> list[ChatMessage]:
    return [
        ChatMessage("system", SYSTEM_TITLE_EXTRACTOR),
        ChatMessage("user", f"文章正文如下：\n\n{article}"),
    ]


def split_title_and_body(generated: str) -> tuple[str, str]:
    """从 LLM 返回的整段文本里切出标题和正文。

    约定：第一行是标题（含 # 等都剥掉），从第二行起是正文。
    如果第一行包含正文味道很重（比如有句号），就保守地把 None 当标题，整段当正文。
    """
    lines = generated.lstrip("﻿").splitlines()
    if not lines:
        return "", ""

    first = lines[0].strip().lstrip("#").strip().strip("《》").strip()
    rest = "\n".join(lines[1:]).strip()

    # 标题启发式：太长或包含完整句号视为正文一部分
    if len(first) > 50 or first.endswith("。") or not first:
        return "", generated.strip()

    return first, rest
