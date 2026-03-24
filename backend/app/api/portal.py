"""
발주처 전용 포털 API (읽기 전용)
토큰 기반 인증으로 발주처가 공사 현황을 실시간 확인합니다.
- 로그인 없이 토큰만으로 접근 가능
- 쓰기 권한 없음
- 민감 정보 제외 (계약 단가 등)
"""
import uuid
import secrets
from datetime import date, datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, func
from pydantic import BaseModel

from app.core.database import AsyncSessionLocal
from app.deps import DB
from app.models.project import Project
from app.models.daily_report import DailyReport, ReportStatus
from app.models.quality import QualityTest, QualityResult
from app.models.inspection import InspectionRequest
from app.models.weather import WeatherAlert
from app.models.evms import EVMSSnapshot
from app.config import settings

router = APIRouter(prefix="/portal", tags=["발주처 포털"])
_bearer = HTTPBearer(auto_error=False)

# 간단한 인메모리 토큰 저장소 (운영에서는 DB/Redis로 교체)
_portal_tokens: dict[str, dict] = {}


def _verify_portal_token(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="포털 토큰이 필요합니다")
    token = credentials.credentials
    info = _portal_tokens.get(token)
    if not info:
        raise HTTPException(status_code=401, detail="유효하지 않은 포털 토큰입니다")
    if datetime.fromisoformat(info["expires_at"]) < datetime.now():
        del _portal_tokens[token]
        raise HTTPException(status_code=401, detail="포털 토큰이 만료되었습니다")
    return info


PortalAuth = Depends(_verify_portal_token)


class TokenCreateRequest(BaseModel):
    project_id: uuid.UUID
    expires_days: int = 30
    label: str = "발주처"


@router.post("/tokens", summary="포털 접근 토큰 발급 (관리자용)")
async def create_portal_token(data: TokenCreateRequest, db: DB):
    """
    발주처에게 공유할 읽기 전용 토큰을 발급합니다.
    이 엔드포인트는 현장 관리자만 호출해야 합니다 (별도 인증 추가 권장).
    """
    r = await db.execute(select(Project).where(Project.id == data.project_id))
    project = r.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")

    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now() + timedelta(days=data.expires_days)).isoformat()
    _portal_tokens[token] = {
        "project_id": str(data.project_id),
        "project_name": project.name,
        "label": data.label,
        "expires_at": expires_at,
    }

    return {
        "token": token,
        "project_name": project.name,
        "expires_at": expires_at,
        "portal_url": f"/portal/dashboard  (Authorization: Bearer {token[:8]}...)",
    }


@router.get("/dashboard", summary="발주처 공사 현황 대시보드")
async def portal_dashboard(auth: dict = PortalAuth, db: DB = None):
    """발주처용 공사 현황 요약 (읽기 전용)"""
    project_id = uuid.UUID(auth["project_id"])
    today = date.today()

    # 프로젝트 기본 정보
    proj_r = await db.execute(select(Project).where(Project.id == project_id))
    project = proj_r.scalar_one_or_none()

    # 최근 작업일보 (3건)
    dr_r = await db.execute(
        select(DailyReport)
        .where(DailyReport.project_id == project_id, DailyReport.status == ReportStatus.CONFIRMED)
        .order_by(DailyReport.report_date.desc())
        .limit(3)
    )
    recent_reports = [
        {"date": str(r.report_date), "weather": r.weather_summary, "work": r.work_content[:100] if r.work_content else ""}
        for r in dr_r.scalars().all()
    ]

    # 품질시험 합격률
    total_qt_r = await db.execute(select(func.count()).where(QualityTest.project_id == project_id))
    total_qt = total_qt_r.scalar() or 0
    pass_qt_r = await db.execute(select(func.count()).where(QualityTest.project_id == project_id, QualityTest.result == QualityResult.PASS))
    pass_qt = pass_qt_r.scalar() or 0

    # EVMS 최신
    evms_r = await db.execute(
        select(EVMSSnapshot).where(EVMSSnapshot.project_id == project_id).order_by(EVMSSnapshot.snapshot_date.desc()).limit(1)
    )
    evms = evms_r.scalar_one_or_none()

    # 활성 날씨 경보
    alert_r = await db.execute(
        select(WeatherAlert).where(WeatherAlert.project_id == project_id, WeatherAlert.alert_date == today, WeatherAlert.acknowledged == False)
    )
    active_alerts = [{"type": a.alert_type, "message": a.message} for a in alert_r.scalars().all()]

    return {
        "project": {
            "name": project.name if project else "-",
            "start_date": str(project.start_date) if project and project.start_date else None,
            "end_date": str(project.end_date) if project and project.end_date else None,
            "status": project.status.value if project else "-",
        },
        "progress": {
            "planned": evms.planned_progress if evms else None,
            "actual": evms.actual_progress if evms else None,
            "spi": evms.spi if evms else None,
            "snapshot_date": str(evms.snapshot_date) if evms else None,
        },
        "quality": {
            "total_tests": total_qt,
            "pass_rate": round(pass_qt / total_qt * 100, 1) if total_qt else None,
        },
        "recent_reports": recent_reports,
        "active_alerts": active_alerts,
        "generated_at": datetime.now().isoformat(),
    }


@router.get("/progress-chart", summary="공정률 추이 데이터")
async def portal_progress_chart(auth: dict = PortalAuth, db: DB = None):
    """발주처용 공정률 추이 차트 데이터"""
    project_id = uuid.UUID(auth["project_id"])
    r = await db.execute(
        select(EVMSSnapshot)
        .where(EVMSSnapshot.project_id == project_id)
        .order_by(EVMSSnapshot.snapshot_date)
        .limit(90)  # 최근 90일
    )
    snapshots = r.scalars().all()
    return {
        "labels": [str(s.snapshot_date) for s in snapshots],
        "planned": [s.planned_progress for s in snapshots],
        "actual": [s.actual_progress for s in snapshots],
        "spi": [s.spi for s in snapshots],
    }
