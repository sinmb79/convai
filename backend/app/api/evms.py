"""EVMS API — PV·EV·AC·SPI·CPI"""
import uuid
from datetime import date
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DB
from app.models.evms import EVMSSnapshot
from app.models.project import Project
from app.services.evms_service import compute_evms, predict_delay, compute_progress_claim

router = APIRouter(prefix="/projects/{project_id}/evms", tags=["EVMS"])


class EVMSRequest(BaseModel):
    snapshot_date: date = date.today()
    actual_cost: float | None = None  # 실제 투입 비용 (없으면 추정)
    save: bool = True                 # DB 저장 여부


class EVMSResponse(BaseModel):
    id: uuid.UUID | None = None
    project_id: uuid.UUID
    snapshot_date: date
    total_budget: float | None
    planned_progress: float | None
    actual_progress: float | None
    pv: float | None
    ev: float | None
    ac: float | None
    spi: float | None
    cpi: float | None
    eac: float | None
    etc: float | None
    detail_json: dict | None = None
    model_config = {"from_attributes": True}


async def _get_project_or_404(project_id: uuid.UUID, db: DB) -> Project:
    r = await db.execute(select(Project).where(Project.id == project_id))
    p = r.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return p


@router.post("/compute", response_model=EVMSResponse)
async def compute_evms_endpoint(
    project_id: uuid.UUID,
    data: EVMSRequest,
    db: DB,
    current_user: CurrentUser,
):
    """EVMS 계산 (옵션: DB 저장)"""
    await _get_project_or_404(project_id, db)

    result = await compute_evms(db, project_id, data.snapshot_date, data.actual_cost)

    if data.save:
        snapshot = EVMSSnapshot(
            project_id=project_id,
            snapshot_date=data.snapshot_date,
            total_budget=result["total_budget"],
            planned_progress=result["planned_progress"],
            actual_progress=result["actual_progress"],
            pv=result["pv"],
            ev=result["ev"],
            ac=result["ac"],
            spi=result["spi"],
            cpi=result["cpi"],
            eac=result["eac"],
            etc=result["etc"],
            detail_json={"tasks": result["detail"]},
        )
        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)

        return EVMSResponse(
            id=snapshot.id,
            project_id=project_id,
            snapshot_date=snapshot.snapshot_date,
            total_budget=snapshot.total_budget,
            planned_progress=snapshot.planned_progress,
            actual_progress=snapshot.actual_progress,
            pv=snapshot.pv, ev=snapshot.ev, ac=snapshot.ac,
            spi=snapshot.spi, cpi=snapshot.cpi,
            eac=snapshot.eac, etc=snapshot.etc,
            detail_json=snapshot.detail_json,
        )

    return EVMSResponse(
        project_id=project_id,
        snapshot_date=data.snapshot_date,
        total_budget=result["total_budget"],
        planned_progress=result["planned_progress"],
        actual_progress=result["actual_progress"],
        pv=result["pv"], ev=result["ev"], ac=result["ac"],
        spi=result["spi"], cpi=result["cpi"],
        eac=result["eac"], etc=result["etc"],
        detail_json={"tasks": result["detail"]},
    )


@router.get("", response_model=list[EVMSResponse])
async def list_snapshots(
    project_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    """EVMS 스냅샷 이력 조회"""
    r = await db.execute(
        select(EVMSSnapshot)
        .where(EVMSSnapshot.project_id == project_id)
        .order_by(EVMSSnapshot.snapshot_date.desc())
    )
    return r.scalars().all()


@router.get("/delay-forecast")
async def delay_forecast(
    project_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    """공기 지연 AI 예측 (최근 EVMS 스냅샷 기반)"""
    r = await db.execute(
        select(EVMSSnapshot)
        .where(EVMSSnapshot.project_id == project_id)
        .order_by(EVMSSnapshot.snapshot_date.desc())
        .limit(1)
    )
    snap = r.scalar_one_or_none()
    if not snap:
        raise HTTPException(status_code=404, detail="EVMS 스냅샷이 없습니다")

    project = await _get_project_or_404(project_id, db)
    planned_end = project.end_date
    if planned_end and not isinstance(planned_end, date):
        from datetime import date as ddate
        planned_end = ddate.fromisoformat(str(planned_end))

    forecast = await predict_delay(
        db, project_id,
        spi=snap.spi,
        planned_end=planned_end,
        snapshot_date=snap.snapshot_date,
    )
    forecast["spi"] = snap.spi
    forecast["cpi"] = snap.cpi
    forecast["snapshot_date"] = str(snap.snapshot_date)
    return forecast


@router.get("/progress-claim")
async def progress_claim(
    project_id: uuid.UUID,
    already_claimed_pct: float = 0.0,
    db: DB = None,
    current_user: CurrentUser = None,
):
    """기성청구 가능 금액 산출"""
    r = await db.execute(
        select(EVMSSnapshot)
        .where(EVMSSnapshot.project_id == project_id)
        .order_by(EVMSSnapshot.snapshot_date.desc())
        .limit(1)
    )
    snap = r.scalar_one_or_none()
    if not snap:
        raise HTTPException(status_code=404, detail="EVMS 스냅샷이 없습니다. /compute 먼저 실행하세요.")

    return await compute_progress_claim(
        total_budget=snap.total_budget or 0,
        actual_progress=snap.actual_progress or 0,
        already_claimed_pct=already_claimed_pct,
    )


@router.get("/latest", response_model=EVMSResponse)
async def latest_snapshot(
    project_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    """최근 EVMS 스냅샷 조회"""
    r = await db.execute(
        select(EVMSSnapshot)
        .where(EVMSSnapshot.project_id == project_id)
        .order_by(EVMSSnapshot.snapshot_date.desc())
        .limit(1)
    )
    snap = r.scalar_one_or_none()
    if not snap:
        raise HTTPException(status_code=404, detail="EVMS 스냅샷이 없습니다. /compute 를 먼저 실행하세요.")
    return snap
