import uuid
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.deps import CurrentUser, DB
from app.models.permit import PermitItem, PermitStatus
from app.models.project import Project
from pydantic import BaseModel
from datetime import date, datetime
from app.services.ai_engine import complete


class PermitCreate(BaseModel):
    permit_type: str
    authority: str | None = None
    required: bool = True
    deadline: date | None = None
    notes: str | None = None
    sort_order: int = 0


class PermitUpdate(BaseModel):
    status: PermitStatus | None = None
    submitted_date: date | None = None
    approved_date: date | None = None
    notes: str | None = None
    deadline: date | None = None


class PermitResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    permit_type: str
    authority: str | None
    required: bool
    deadline: date | None
    status: PermitStatus
    submitted_date: date | None
    approved_date: date | None
    notes: str | None
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


router = APIRouter(prefix="/projects/{project_id}/permits", tags=["인허가 체크리스트"])


async def _get_project_or_404(project_id: uuid.UUID, db: DB) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return p


@router.get("", response_model=list[PermitResponse])
async def list_permits(project_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(
        select(PermitItem).where(PermitItem.project_id == project_id).order_by(PermitItem.sort_order)
    )
    return result.scalars().all()


@router.post("", response_model=PermitResponse, status_code=status.HTTP_201_CREATED)
async def create_permit(project_id: uuid.UUID, data: PermitCreate, db: DB, current_user: CurrentUser):
    await _get_project_or_404(project_id, db)
    permit = PermitItem(**data.model_dump(), project_id=project_id)
    db.add(permit)
    await db.commit()
    await db.refresh(permit)
    return permit


@router.put("/{permit_id}", response_model=PermitResponse)
async def update_permit(project_id: uuid.UUID, permit_id: uuid.UUID, data: PermitUpdate, db: DB, current_user: CurrentUser):
    result = await db.execute(select(PermitItem).where(PermitItem.id == permit_id, PermitItem.project_id == project_id))
    permit = result.scalar_one_or_none()
    if not permit:
        raise HTTPException(status_code=404, detail="인허가 항목을 찾을 수 없습니다")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(permit, field, value)
    await db.commit()
    await db.refresh(permit)
    return permit


@router.delete("/{permit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permit(project_id: uuid.UUID, permit_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(PermitItem).where(PermitItem.id == permit_id, PermitItem.project_id == project_id))
    permit = result.scalar_one_or_none()
    if not permit:
        raise HTTPException(status_code=404, detail="인허가 항목을 찾을 수 없습니다")
    await db.delete(permit)
    await db.commit()


class PermitDerivationRequest(BaseModel):
    work_types: list[str]
    construction_type: str
    start_date: date | None = None
    auto_create: bool = True


@router.post("/derive", response_model=list[PermitResponse], status_code=status.HTTP_201_CREATED)
async def derive_permits(
    project_id: uuid.UUID,
    data: PermitDerivationRequest,
    db: DB,
    current_user: CurrentUser,
):
    """공종 입력 → 필요 인허가 항목 AI 자동 도출"""
    await _get_project_or_404(project_id, db)

    system = """당신은 건설공사 인허가 전문가입니다.
공사 정보를 보고 필요한 인허가 항목을 JSON 배열로만 반환하세요.
각 항목: {"permit_type": "도로점용허가", "authority": "관할 시·군·구청", "notes": "착공 30일 전 신청"}
법령 근거를 notes에 간략히 포함하세요."""

    user_msg = (
        f"공사 유형: {data.construction_type}\n"
        f"주요 공종: {', '.join(data.work_types)}\n"
        f"착공 예정: {data.start_date or '미정'}\n\n"
        "이 공사에 필요한 인허가 항목을 모두 도출해주세요. JSON 배열로만 반환하세요."
    )

    raw = await complete(
        messages=[{"role": "user", "content": user_msg}],
        system=system,
        temperature=0.2,
    )

    import json, re
    json_match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not json_match:
        raise HTTPException(status_code=500, detail="AI 응답 파싱 실패")

    items_data = json.loads(json_match.group())

    created = []
    if data.auto_create:
        for idx, item in enumerate(items_data):
            permit = PermitItem(
                project_id=project_id,
                permit_type=item.get("permit_type", "미정"),
                authority=item.get("authority"),
                required=True,
                notes=item.get("notes"),
                sort_order=idx,
                deadline=data.start_date,
            )
            db.add(permit)
            created.append(permit)
        await db.commit()
        for p in created:
            await db.refresh(p)

    return created
