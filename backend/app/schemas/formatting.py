"""排版相关 Pydantic schema。"""

from pydantic import BaseModel, Field


class TemplateInfo(BaseModel):
    id: str
    name: str
    description: str


class TemplateList(BaseModel):
    items: list[TemplateInfo]


class FormatRequest(BaseModel):
    template_id: str
    title: str | None = Field(default=None, max_length=200)
    content: str = Field(min_length=1, description="markdown 正文")
    full_page: bool = Field(default=False, description="true 时包成完整 .html 文件")


class FormatResponse(BaseModel):
    template_id: str
    html: str
    title: str | None = None
