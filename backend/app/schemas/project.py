import uuid
from datetime import date, datetime
from pydantic import BaseModel
from app.models.project import ProjectStatus, ConstructionType


class WBSItemCreate(BaseModel):
    parent_id: uuid.UUID | None = None
    code: str
    name: str
    level: int = 1
    unit: str | None = None
    design_qty: float | None = None
    unit_price: float | None = None
    sort_order: int = 0


class WBSItemResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    parent_id: uuid.UUID | None
    code: str
    name: str
    level: int
    unit: str | None
    design_qty: float | None
    unit_price: float | None
    sort_order: int
    children: list["WBSItemResponse"] = []

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    name: str
    code: str
    client_profile_id: uuid.UUID | None = None
    construction_type: ConstructionType = ConstructionType.OTHER
    contract_amount: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    location_address: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    client_profile_id: uuid.UUID | None = None
    construction_type: ConstructionType | None = None
    contract_amount: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    location_address: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    status: ProjectStatus | None = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    client_profile_id: uuid.UUID | None
    construction_type: ConstructionType
    contract_amount: int | None
    start_date: date | None
    end_date: date | None
    location_address: str | None
    location_lat: float | None
    location_lng: float | None
    status: ProjectStatus
    owner_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
