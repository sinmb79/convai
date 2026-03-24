import uuid
from datetime import date, datetime
from pydantic import BaseModel
from app.models.inspection import InspectionResult, InspectionStatus


class InspectionCreate(BaseModel):
    wbs_item_id: uuid.UUID | None = None
    inspection_type: str
    requested_date: date
    location_detail: str | None = None
    checklist_items: list | None = None
    notes: str | None = None


class InspectionGenerateRequest(BaseModel):
    wbs_item_id: uuid.UUID | None = None
    inspection_type: str
    requested_date: date
    location_detail: str | None = None


class InspectionUpdate(BaseModel):
    checklist_items: list | None = None
    result: InspectionResult | None = None
    inspector_name: str | None = None
    notes: str | None = None
    status: InspectionStatus | None = None


class InspectionResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    wbs_item_id: uuid.UUID | None
    inspection_type: str
    requested_date: date
    location_detail: str | None
    checklist_items: list | None
    result: InspectionResult | None
    inspector_name: str | None
    notes: str | None
    ai_generated: bool
    status: InspectionStatus
    pdf_s3_key: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
