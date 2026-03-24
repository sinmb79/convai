import uuid
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.deps import CurrentUser, DB
from app.models.permit import PermitItem, PermitStatus
from app.models.project import Project
from pydantic import BaseModel
from datetime import date, datetime


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
