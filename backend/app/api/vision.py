"""
Vision AI API — Level 1 (사진 분류) + Level 2 (안전장비 감지)
"""
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.deps import CurrentUser, DB
from app.models.project import Project
from app.models.daily_report import DailyReport, DailyReportPhoto
from app.services.vision_service import classify_photo, analyze_safety, compare_with_drawing

router = APIRouter(prefix="/projects/{project_id}/vision", tags=["Vision AI"])

COMPARISON_TYPES = {"rebar": "철근 배근", "formwork": "거푸집", "general": "일반 비교"}

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
MAX_SIZE_MB = 10


async def _get_project_or_404(project_id: uuid.UUID, db: DB) -> Project:
    r = await db.execute(select(Project).where(Project.id == project_id))
    p = r.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return p


@router.post("/classify")
async def classify_field_photo(
    project_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    location_hint: str | None = Form(None),
    daily_report_id: uuid.UUID | None = Form(None),
):
    """
    현장 사진 분류 (Vision AI Level 1)
    - 공종 자동 분류
    - 안전장비 착용 여부 1차 확인
    - 작업일보 캡션 자동 생성
    - daily_report_id 제공 시 해당 일보에 사진 자동 첨부
    """
    await _get_project_or_404(project_id, db)

    # 파일 검증
    content_type = file.content_type or "image/jpeg"
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용: {', '.join(ALLOWED_TYPES)}"
        )

    image_data = await file.read()
    if len(image_data) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"파일 크기가 {MAX_SIZE_MB}MB를 초과합니다")

    # Vision AI 분류
    result = await classify_photo(
        image_data=image_data,
        media_type=content_type,
        location_hint=location_hint,
    )

    # 작업일보에 사진 첨부 (daily_report_id 제공 시)
    if daily_report_id:
        dr = await db.execute(
            select(DailyReport).where(
                DailyReport.id == daily_report_id,
                DailyReport.project_id == project_id,
            )
        )
        report = dr.scalar_one_or_none()
        if report:
            # 사진 수 카운트
            photos_q = await db.execute(
                select(DailyReportPhoto).where(DailyReportPhoto.daily_report_id == daily_report_id)
            )
            existing = photos_q.scalars().all()

            photo = DailyReportPhoto(
                daily_report_id=daily_report_id,
                s3_key=f"vision/{project_id}/{daily_report_id}/{file.filename or 'photo.jpg'}",
                caption=result.get("caption", ""),
                sort_order=len(existing),
            )
            db.add(photo)
            await db.commit()
            result["attached_to_report"] = str(daily_report_id)

    return JSONResponse(content=result)


@router.post("/compare-drawing")
async def compare_drawing(
    project_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    field_photo: UploadFile = File(..., description="현장 사진"),
    drawing: UploadFile = File(..., description="설계 도면 이미지"),
    comparison_type: str = Form("rebar", description="rebar/formwork/general"),
):
    """
    Vision AI Level 3 — 설계 도면 vs 현장 사진 비교 보조 판독
    철근 배근, 거푸집 치수 등을 도면과 1차 비교합니다.
    ⚠️ 최종 합격/불합격 판정은 현장 책임자가 합니다.
    """
    await _get_project_or_404(project_id, db)

    if comparison_type not in COMPARISON_TYPES:
        raise HTTPException(status_code=400, detail=f"comparison_type은 {list(COMPARISON_TYPES.keys())} 중 하나여야 합니다")

    field_data   = await field_photo.read()
    drawing_data = await drawing.read()

    if len(field_data) > MAX_SIZE_MB * 1024 * 1024 or len(drawing_data) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"파일 크기가 {MAX_SIZE_MB}MB를 초과합니다")

    result = await compare_with_drawing(
        field_photo=field_data,
        drawing_image=drawing_data,
        comparison_type=comparison_type,
        field_media_type=field_photo.content_type or "image/jpeg",
        drawing_media_type=drawing.content_type or "image/jpeg",
    )
    return JSONResponse(content=result)


@router.post("/safety-check")
async def safety_check(
    project_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    file: UploadFile = File(...),
):
    """
    안전장비 착용 감지 (Vision AI Level 2)
    안전모/안전조끼 착용 여부를 분석하고 위반 사항을 반환합니다.
    최종 판정은 현장 책임자가 합니다.
    """
    await _get_project_or_404(project_id, db)

    content_type = file.content_type or "image/jpeg"
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다")

    image_data = await file.read()
    if len(image_data) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"파일 크기가 {MAX_SIZE_MB}MB를 초과합니다")

    result = await analyze_safety(image_data=image_data, media_type=content_type)
    result["disclaimer"] = "이 결과는 AI 1차 분석이며, 최종 판정은 현장 책임자가 합니다."
    return JSONResponse(content=result)
