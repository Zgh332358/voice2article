"""排版端点：列模板 + 应用模板生成 HTML。"""

from fastapi import APIRouter, status

from app.api.deps import CurrentUser
from app.core.errors import AppError
from app.schemas import FormatRequest, FormatResponse, TemplateInfo, TemplateList
from app.services.formatting import (
    get_template,
    list_templates,
    render_full_document,
    render_full_html_page,
)

router = APIRouter(prefix="/formatting", tags=["formatting"])


class TemplateNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "template_not_found"


@router.get("/templates", response_model=TemplateList, summary="列出所有可用排版模板")
async def get_templates(_: CurrentUser) -> TemplateList:
    return TemplateList(
        items=[
            TemplateInfo(id=t.id, name=t.name, description=t.description)
            for t in list_templates()
        ]
    )


@router.post(
    "/apply",
    response_model=FormatResponse,
    summary="把 markdown 渲染成 inline-style HTML",
)
async def apply_template(payload: FormatRequest, _: CurrentUser) -> FormatResponse:
    template = get_template(payload.template_id)
    if template is None:
        raise TemplateNotFoundError(f"未知模板 id：{payload.template_id}")

    body_html = render_full_document(
        title=payload.title,
        body_markdown=payload.content,
        template=template,
    )
    if payload.full_page:
        body_html = render_full_html_page(title=payload.title, body_html=body_html)

    return FormatResponse(template_id=template.id, html=body_html, title=payload.title)
