"""
EVMS (Earned Value Management System) — Phase 3 완전 자동화
PV, EV, AC, SPI, CPI 산출 + 공정 지연 예측 AI + 기성청구 자동 알림
"""
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.project import Project


async def predict_delay(
    db: AsyncSession,
    project_id,
    spi: float,
    planned_end: date | None,
    snapshot_date: date,
) -> dict:
    """
    SPI 기반 공기 지연 예측.
    spi < 1 이면 지연, 남은 기간을 SPI로 나눠 예상 준공일 계산.
    """
    if not planned_end or spi is None or spi <= 0:
        return {"delay_days": None, "predicted_end": None, "status": "예측 불가"}

    remaining_days = (planned_end - snapshot_date).days
    if remaining_days <= 0:
        return {"delay_days": 0, "predicted_end": str(planned_end), "status": "준공 예정일 경과"}

    predicted_remaining = remaining_days / spi
    predicted_end = snapshot_date + timedelta(days=int(predicted_remaining))
    delay_days = (predicted_end - planned_end).days

    if delay_days > 0:
        status = f"{delay_days}일 지연 예상"
    elif delay_days < -3:
        status = f"{abs(delay_days)}일 조기 준공 예상"
    else:
        status = "정상 진행"

    return {
        "delay_days": delay_days,
        "predicted_end": str(predicted_end),
        "status": status,
    }


async def compute_progress_claim(
    total_budget: float,
    actual_progress: float,
    already_claimed_pct: float = 0.0,
) -> dict:
    """
    기성청구 가능 금액 산출.
    기성청구 가능 금액 = 총예산 × (실제 공정률 - 기청구 공정률)
    """
    claimable_pct = max(0.0, actual_progress - already_claimed_pct)
    claimable_amount = total_budget * (claimable_pct / 100)
    return {
        "actual_progress": actual_progress,
        "already_claimed_pct": already_claimed_pct,
        "claimable_pct": round(claimable_pct, 1),
        "claimable_amount": round(claimable_amount, 0),
        "claimable_amount_formatted": f"{claimable_amount:,.0f}원",
    }


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


async def compute_evms(
    db: AsyncSession,
    project_id,
    snapshot_date: date,
    actual_cost: float | None = None,
) -> dict:
    """
    WBS/Task 기반 EVMS 지표 계산.

    PV = 총예산 × 기준일 계획 공정률
    EV = 총예산 × 기준일 실제 공정률
    AC = 실제 투입 비용 (입력값 없으면 EV × 0.95 추정)

    반환: {pv, ev, ac, spi, cpi, eac, etc, planned_progress, actual_progress, detail}
    """
    import uuid
    pid = uuid.UUID(str(project_id))
    today = snapshot_date

    # 프로젝트 정보
    proj_r = await db.execute(select(Project).where(Project.id == pid))
    project = proj_r.scalar_one_or_none()
    if not project:
        raise ValueError("프로젝트를 찾을 수 없습니다")

    total_budget = float(project.contract_amount or 0)

    # 태스크 조회
    tasks_r = await db.execute(select(Task).where(Task.project_id == pid))
    tasks = tasks_r.scalars().all()

    if not tasks:
        return {
            "total_budget": total_budget,
            "planned_progress": 0.0,
            "actual_progress": 0.0,
            "pv": 0.0, "ev": 0.0, "ac": 0.0,
            "spi": None, "cpi": None,
            "eac": None, "etc": None,
            "detail": [],
        }

    # 태스크별 PV, EV 계산
    total_tasks = len(tasks)
    planned_pct_sum = 0.0
    actual_pct_sum = 0.0
    detail = []

    for task in tasks:
        # 계획 공정률: 기준일 기준 planned_start ~ planned_end 선형 보간
        p_start = task.planned_start
        p_end   = task.planned_end
        task_planned_pct = 0.0

        if p_start and p_end:
            ps = p_start if isinstance(p_start, date) else date.fromisoformat(str(p_start))
            pe = p_end   if isinstance(p_end,   date) else date.fromisoformat(str(p_end))

            if today < ps:
                task_planned_pct = 0.0
            elif today >= pe:
                task_planned_pct = 100.0
            else:
                total_days = (pe - ps).days or 1
                elapsed    = (today - ps).days
                task_planned_pct = _clamp(elapsed / total_days * 100, 0.0, 100.0)
        else:
            task_planned_pct = 0.0

        task_actual_pct = float(task.progress_pct or 0.0)
        planned_pct_sum += task_planned_pct
        actual_pct_sum  += task_actual_pct

        detail.append({
            "task_id":   str(task.id),
            "task_name": task.name,
            "planned_pct": round(task_planned_pct, 1),
            "actual_pct":  round(task_actual_pct,  1),
            "is_critical": task.is_critical,
        })

    planned_progress = round(planned_pct_sum / total_tasks, 1)
    actual_progress  = round(actual_pct_sum  / total_tasks, 1)

    pv = total_budget * (planned_progress / 100) if total_budget else None
    ev = total_budget * (actual_progress  / 100) if total_budget else None

    # AC: 입력값 없으면 EV × 1.05 (5% 비용 초과 가정)
    if actual_cost is not None:
        ac = float(actual_cost)
    elif ev is not None:
        ac = ev * 1.05
    else:
        ac = None

    spi = round(ev / pv, 3) if (pv and pv > 0 and ev is not None) else None
    cpi = round(ev / ac, 3) if (ac and ac > 0 and ev is not None) else None

    # EAC (Estimate at Completion) = 총예산 / CPI
    eac = round(total_budget / cpi, 0) if (cpi and cpi > 0 and total_budget) else None
    # ETC (Estimate to Completion) = EAC - AC
    etc = round(eac - ac, 0) if (eac is not None and ac is not None) else None

    return {
        "total_budget":      total_budget,
        "planned_progress":  planned_progress,
        "actual_progress":   actual_progress,
        "pv":  round(pv, 0) if pv is not None else None,
        "ev":  round(ev, 0) if ev is not None else None,
        "ac":  round(ac, 0) if ac is not None else None,
        "spi": spi,
        "cpi": cpi,
        "eac": eac,
        "etc": etc,
        "detail": detail,
    }
