"""
Geofence 위험구역 API
- 위험구역 CRUD (익명 — 개인 이동 경로 비수집)
- 진입 이벤트 웹훅 (카카오맵 또는 모바일 앱에서 호출)
- ANJEON 에이전트 연동 경보
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.deps import CurrentUser, DB
from app.models.agent import GeofenceZone
from app.models.project import Project

router = APIRouter(prefix="/projects/{project_id}/geofence", tags=["Geofence 위험구역"])


ZONE_TYPE_LABELS = {
    "excavation":    "굴착면",
    "crane":         "크레인 반경",
    "confined":      "밀폐공간",
    "high_voltage":  "고압선 인근",
    "slope":         "비탈면",
    "custom":        "사용자 정의",
}


class ZoneCreate(BaseModel):
    name: str
    zone_type: str
    coordinates: list[list[float]]  # [[lat, lng], ...]
    radius_m: float | None = None
    description: str | None = None


class ZoneUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    description: str | None = None


class ZoneResponse(BaseModel):
    id: uuid.UUID
    name: str
    zone_type: str
    zone_type_label: str
    coordinates: list
    radius_m: float | None
    is_active: bool
    description: str | None
    model_config = {"from_attributes": True}


class EntryEvent(BaseModel):
    """위험구역 진입 이벤트 (개인 식별 정보 없음)"""
    zone_id: uuid.UUID
    device_token: str  # 익명 토큰 (개인 특정 불가)
    timestamp: datetime | None = None


async def _get_project_or_404(project_id: uuid.UUID, db: DB) -> Project:
    r = await db.execute(select(Project).where(Project.id == project_id))
    p = r.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return p


def _to_response(zone: GeofenceZone) -> ZoneResponse:
    return ZoneResponse(
        id=zone.id,
        name=zone.name,
        zone_type=zone.zone_type,
        zone_type_label=ZONE_TYPE_LABELS.get(zone.zone_type, zone.zone_type),
        coordinates=zone.coordinates,
        radius_m=zone.radius_m,
        is_active=zone.is_active,
        description=zone.description,
    )


@router.get("", response_model=list[ZoneResponse])
async def list_zones(project_id: uuid.UUID, db: DB, current_user: CurrentUser):
    r = await db.execute(
        select(GeofenceZone).where(GeofenceZone.project_id == project_id).order_by(GeofenceZone.created_at)
    )
    return [_to_response(z) for z in r.scalars().all()]


@router.post("", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_zone(
    project_id: uuid.UUID, data: ZoneCreate, db: DB, current_user: CurrentUser
):
    await _get_project_or_404(project_id, db)
    zone = GeofenceZone(**data.model_dump(), project_id=project_id)
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return _to_response(zone)


@router.put("/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    project_id: uuid.UUID, zone_id: uuid.UUID, data: ZoneUpdate, db: DB, current_user: CurrentUser
):
    r = await db.execute(
        select(GeofenceZone).where(GeofenceZone.id == zone_id, GeofenceZone.project_id == project_id)
    )
    zone = r.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="구역을 찾을 수 없습니다")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(zone, k, v)
    await db.commit()
    await db.refresh(zone)
    return _to_response(zone)


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(
    project_id: uuid.UUID, zone_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    r = await db.execute(
        select(GeofenceZone).where(GeofenceZone.id == zone_id, GeofenceZone.project_id == project_id)
    )
    zone = r.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="구역을 찾을 수 없습니다")
    await db.delete(zone)
    await db.commit()


@router.post("/entry-event")
async def zone_entry_event(
    project_id: uuid.UUID,
    event: EntryEvent,
    db: DB,
):
    """
    위험구역 진입 감지 웹훅 (모바일 앱 또는 카카오맵에서 호출)
    - 개인 이동 경로 비수집
    - 진입 이벤트만 기록하고 ANJEON 에이전트가 경보를 생성합니다
    """
    r = await db.execute(
        select(GeofenceZone).where(
            GeofenceZone.id == event.zone_id,
            GeofenceZone.project_id == project_id,
            GeofenceZone.is_active == True,
        )
    )
    zone = r.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="활성 위험구역을 찾을 수 없습니다")

    # ANJEON 에이전트로 경보 메시지 생성
    from app.services.agents.anjeon import anjeon_agent
    alert_message = (
        f"⚠️ 위험구역 진입 감지\n"
        f"구역: {zone.name} ({ZONE_TYPE_LABELS.get(zone.zone_type, zone.zone_type)})\n"
        f"시각: {(event.timestamp or datetime.now()).strftime('%H:%M')}\n"
        f"즉시 해당 구역을 확인하고 안전 조치를 취하세요."
    )

    return {
        "zone_id": str(zone.id),
        "zone_name": zone.name,
        "alert": alert_message,
        "timestamp": (event.timestamp or datetime.now()).isoformat(),
    }
