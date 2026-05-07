"""公众号排版引擎。

把 LLM 生成的 markdown（标题 + 正文）转成内联样式 HTML，
可以直接粘贴到微信公众号编辑器（不依赖外链 CSS）。

设计要点：
- markdown-it-py 把 markdown 解析成 token，再用主题表渲染
- 所有样式都用 inline style，避免微信清洗 <style> 块
- 段落、标题、列表、引用、强调全部走主题表，方便后续加新模板
"""

from __future__ import annotations

import html
from collections.abc import Mapping
from dataclasses import dataclass

from markdown_it import MarkdownIt


@dataclass(frozen=True)
class Template:
    id: str
    name: str
    description: str
    styles: Mapping[str, str]  # 标签名 → inline css


# ---------- 主题表 ----------

_BASE_BODY = (
    "max-width: 100%; padding: 0 4px; "
    "font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', "
    "Arial, 'Microsoft YaHei', sans-serif; "
    "color: #333; line-height: 1.75; font-size: 16px;"
)

MINIMAL = Template(
    id="minimal",
    name="简约",
    description="干净的黑白灰排版，适合长文阅读。",
    styles={
        "body": _BASE_BODY,
        "h1": "font-size: 22px; font-weight: 700; color: #1a1a1a; margin: 28px 0 16px;",
        "h2": "font-size: 18px; font-weight: 600; color: #1a1a1a; margin: 24px 0 12px; "
              "border-left: 4px solid #1a1a1a; padding-left: 10px;",
        "h3": "font-size: 16px; font-weight: 600; color: #333; margin: 20px 0 10px;",
        "p": "margin: 14px 0; text-align: justify; word-break: break-word;",
        "ul": "margin: 12px 0; padding-left: 24px;",
        "ol": "margin: 12px 0; padding-left: 24px;",
        "li": "margin: 6px 0;",
        "blockquote": "margin: 16px 0; padding: 12px 16px; background: #f7f7f7; "
                      "border-left: 4px solid #ccc; color: #555;",
        "strong": "font-weight: 700; color: #1a1a1a;",
        "em": "font-style: italic; color: #555;",
        "code": "background: #f4f4f4; padding: 2px 6px; border-radius: 3px; "
                "font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 14px;",
        "hr": "margin: 24px 0; border: 0; border-top: 1px solid #e5e5e5;",
        "a": "color: #2962ff; text-decoration: none;",
    },
)

BUSINESS = Template(
    id="business",
    name="商务蓝",
    description="正式的蓝色主调，适合品牌、企业内容。",
    styles={
        "body": _BASE_BODY,
        "h1": "font-size: 22px; font-weight: 700; color: #003366; margin: 28px 0 16px; "
              "text-align: center;",
        "h2": "font-size: 18px; font-weight: 600; color: #003366; margin: 24px 0 12px; "
              "background: #eaf2fa; padding: 8px 12px; border-radius: 4px;",
        "h3": "font-size: 16px; font-weight: 600; color: #003366; margin: 20px 0 10px;",
        "p": "margin: 14px 0; text-align: justify; word-break: break-word;",
        "ul": "margin: 12px 0; padding-left: 24px;",
        "ol": "margin: 12px 0; padding-left: 24px;",
        "li": "margin: 6px 0;",
        "blockquote": "margin: 16px 0; padding: 12px 16px; background: #f0f6fc; "
                      "border-left: 4px solid #003366; color: #444;",
        "strong": "font-weight: 700; color: #003366;",
        "em": "font-style: italic; color: #555;",
        "code": "background: #eef3f8; padding: 2px 6px; border-radius: 3px; "
                "font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 14px; "
                "color: #003366;",
        "hr": "margin: 24px 0; border: 0; border-top: 2px solid #003366;",
        "a": "color: #003366; text-decoration: underline;",
    },
)

TECH = Template(
    id="tech",
    name="科技绿",
    description="深色辅以荧光绿，适合 AI / 技术类内容。",
    styles={
        "body": _BASE_BODY,
        "h1": "font-size: 22px; font-weight: 700; color: #0d4f3c; margin: 28px 0 16px;",
        "h2": "font-size: 18px; font-weight: 600; color: #0d4f3c; margin: 24px 0 12px; "
              "border-bottom: 2px solid #00b388; padding-bottom: 6px;",
        "h3": "font-size: 16px; font-weight: 600; color: #0d4f3c; margin: 20px 0 10px;",
        "p": "margin: 14px 0; text-align: justify; word-break: break-word;",
        "ul": "margin: 12px 0; padding-left: 24px;",
        "ol": "margin: 12px 0; padding-left: 24px;",
        "li": "margin: 6px 0;",
        "blockquote": "margin: 16px 0; padding: 12px 16px; background: #f0fdf4; "
                      "border-left: 4px solid #00b388; color: #444;",
        "strong": "font-weight: 700; color: #0d4f3c;",
        "em": "font-style: italic; color: #00b388;",
        "code": "background: #f0fdf4; padding: 2px 6px; border-radius: 3px; "
                "font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 14px; "
                "color: #0d4f3c;",
        "hr": "margin: 24px 0; border: 0; border-top: 1px dashed #00b388;",
        "a": "color: #00b388; text-decoration: none;",
    },
)


TEMPLATES: dict[str, Template] = {t.id: t for t in (MINIMAL, BUSINESS, TECH)}


def list_templates() -> list[Template]:
    return list(TEMPLATES.values())


def get_template(template_id: str) -> Template | None:
    return TEMPLATES.get(template_id)


# ---------- 渲染 ----------

_md = MarkdownIt("commonmark", {"breaks": True, "html": False})


def render_markdown_to_html(markdown_text: str, template: Template) -> str:
    """把 markdown 渲染成单段 inline-style HTML。

    实现思路：先用 markdown-it 拿原始 HTML，再做轻量字符串替换把样式注入。
    复杂用例（嵌套列表 / 表格）这里没追求完美，MVP 阶段够用。
    """
    raw = _md.render(markdown_text or "")

    # 顺序敏感：先 h1/h2/h3，再 p / ul / ol / li / blockquote / strong / em / code / hr / a
    # 用 str.replace 简单可靠（不引入 HTML 解析器）
    for tag in ("h1", "h2", "h3", "p", "ul", "ol", "li", "blockquote", "strong", "em", "code", "hr"):
        style = template.styles.get(tag)
        if not style:
            continue
        if tag == "hr":
            raw = raw.replace("<hr>", f'<hr style="{style}">')
            raw = raw.replace("<hr />", f'<hr style="{style}" />')
            continue
        raw = raw.replace(f"<{tag}>", f'<{tag} style="{style}">')

    # a 标签需要保留 href，单独处理：把 <a href="..."> 变成带 style 的
    a_style = template.styles.get("a", "")
    if a_style:
        raw = raw.replace("<a ", f'<a style="{a_style}" ')

    body_style = template.styles.get("body", "")
    return f'<section style="{body_style}">\n{raw.strip()}\n</section>'


def render_full_document(
    *,
    title: str | None,
    body_markdown: str,
    template: Template,
) -> str:
    """如果有标题，作为 H1 拼到正文最前。"""
    title_md = f"# {title}\n\n" if title else ""
    return render_markdown_to_html(title_md + body_markdown, template)


def render_full_html_page(
    *,
    title: str | None,
    body_html: str,
) -> str:
    """把 body_html 包成完整的 .html 文件，方便用户下载到本地预览。"""
    page_title = html.escape(title or "公众号文章")
    return (
        "<!doctype html>\n"
        f"<html><head><meta charset=\"utf-8\"><title>{page_title}</title></head>\n"
        f"<body style=\"margin: 0; padding: 24px; background: #f5f5f5;\">\n"
        f"<div style=\"max-width: 720px; margin: 0 auto; background: #fff; "
        f"padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);\">\n"
        f"{body_html}\n"
        "</div>\n</body></html>\n"
    )
