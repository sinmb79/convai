"""준공도서 패키지 API"""
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io
from sqlalchemy import select

from app.deps import CurrentUser, DB
from app.models.project import Project
from app.services.completion_service import build_completion_package

router = APIRouter(prefix="/projects/{project_id}/completion", tags=["준공도서"])


async def _get_project_or_404(project_id: uuid.UUID, db: DB) -> Project:
    r = await db.execute(select(Project).where(Project.id == project_id))
    p = r.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return p


@router.get("/download")
async def download_completion_package(
    project_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """
    준공도서 ZIP 패키지 다운로드
    포함 문서:
    - 준공 요약 (전체 실적)
    - 품질시험 목록 (전체)
    - 검측 이력 (전체)
    - 인허가 현황 (전체)
    """
    await _get_project_or_404(project_id, db)
    zip_bytes, filename = await build_completion_package(db, project_id)

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.get("/checklist")
async def completion_checklist(
    project_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """
    준공 준비 체크리스트 — 부족한 서류/데이터 현황 반환
    """
    from app.models.daily_report import DailyReport
    from app.models.quality import QualityTest
    from app.models.inspection import InspectionRequest, InspectionStatus
    from app.models.permit import PermitItem, PermitStatus
    from sqlalchemy import func

    await _get_project_or_404(project_id, db)

    async def count(model, where):
        r = await db.execute(select(func.count()).where(*where))
        return r.scalar() or 0

    total_dr    = await count(DailyReport, [DailyReport.project_id == project_id])
    total_qt    = await count(QualityTest, [QualityTest.project_id == project_id])
    total_insp  = await count(InspectionRequest, [InspectionRequest.project_id == project_id])
    done_insp   = await count(InspectionRequest, [
        InspectionRequest.project_id == project_id,
        InspectionRequest.status == InspectionStatus.COMPLETED,
    ])
    total_per   = await count(PermitItem, [PermitItem.project_id == project_id])
    approved_per = await count(PermitItem, [
        PermitItem.project_id == project_id,
        PermitItem.status == PermitStatus.APPROVED,
    ])

    checks = [
        {
            "item": "작업일보",
            "count": total_dr,
            "status": "준비완료" if total_dr > 0 else "누락",
            "ok": total_dr > 0,
        },
        {
            "item": "품질시험 기록",
            "count": total_qt,
            "status": "준비완료" if total_qt > 0 else "누락",
            "ok": total_qt > 0,
        },
        {
            "item": "검측 완료",
            "count": f"{done_insp}/{total_insp}",
            "status": "완료" if total_insp > 0 and done_insp == total_insp else f"미완료 {total_insp - done_insp}건",
            "ok": total_insp > 0 and done_insp == total_insp,
        },
        {
            "item": "인허가 취득",
            "count": f"{approved_per}/{total_per}",
            "status": "완료" if total_per > 0 and approved_per == total_per else f"미취득 {total_per - approved_per}건",
            "ok": total_per > 0 and approved_per == total_per,
        },
    ]

    all_ok = all(c["ok"] for c in checks)
    return {
        "ready": all_ok,
        "summary": "준공 준비 완료" if all_ok else "준공 서류 미비 항목이 있습니다",
        "checks": checks,
    }
