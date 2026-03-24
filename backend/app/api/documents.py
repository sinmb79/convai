"""
설계도서 파싱 + HWP 출력 API
"""
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select

from app.deps import CurrentUser, DB
from app.models.project import Project
from app.services.document_parser import (
    parse_design_document_text,
    parse_design_document_image,
    convert_to_hwp,
)
from app.services.pdf_service import _render_html, _html_to_pdf

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["설계도서"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_MB = 20


async def _get_project_or_404(project_id: uuid.UUID, db: DB) -> Project:
    r = await db.execute(select(Project).where(Project.id == project_id))
    p = r.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return p


@router.post("/parse-image")
async def parse_document_image(
    project_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    file: UploadFile = File(..., description="도면 이미지 (JPG/PNG)"),
):
    """
    설계 도면 이미지 → 공종/수량/규격 자동 추출 (Claude Vision)
    """
    await _get_project_or_404(project_id, db)

    content_type = file.content_type or "image/jpeg"
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="JPG, PNG, WEBP 이미지만 지원합니다")

    image_data = await file.read()
    if len(image_data) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"파일 크기가 {MAX_SIZE_MB}MB를 초과합니다")

    result = await parse_design_document_image(image_data, content_type)
    return result


@router.post("/parse-text")
async def parse_document_text(
    project_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    file: UploadFile = File(..., description="설계도서 텍스트 파일 (TXT/MD)"),
):
    """
    설계도서 텍스트 파일 → 공종/수량/규격 자동 추출
    """
    await _get_project_or_404(project_id, db)

    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    result = await parse_design_document_text(text)
    return result


class HWPRequest(BaseModel):
    html_content: str
    filename: str = "document.hwp"


@router.post("/export-hwp")
async def export_hwp(
    project_id: uuid.UUID,
    data: HWPRequest,
    db: DB,
    current_user: CurrentUser,
):
    """
    HTML → HWP 변환 (Pandoc 필요)
    보고서나 일보를 HWP 형식으로 내보냅니다.
    """
    await _get_project_or_404(project_id, db)

    try:
        hwp_bytes = convert_to_hwp(data.html_content)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return Response(
        content=hwp_bytes,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{data.filename}"},
    )
