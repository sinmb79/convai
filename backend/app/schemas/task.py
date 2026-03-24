import uuid
from datetime import date, datetime
from pydantic import BaseModel
from app.models.task import DependencyType


class TaskCreate(BaseModel):
    wbs_item_id: uuid.UUID | None = None
    name: str
    planned_start: date | None = None
    planned_end: date | None = None
    is_milestone: bool = False
    sort_order: int = 0


class TaskUpdate(BaseModel):
    name: str | None = None
    planned_start: date | None = None
    planned_end: date | None = None
    actual_start: date | None = None
    actual_end: date | None = None
    progress_pct: float | None = None
    is_milestone: bool | None = None
    sort_order: int | None = None


class TaskDependencyCreate(BaseModel):
    predecessor_id: uuid.UUID
    successor_id: uuid.UUID
    dependency_type: DependencyType = DependencyType.FS
    lag_days: int = 0


class TaskResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    wbs_item_id: uuid.UUID | None
    name: str
    planned_start: date | None
    planned_end: date | None
    actual_start: date | None
    actual_end: date | None
    progress_pct: float
    is_milestone: bool
    is_critical: bool
    early_start: date | None
    early_finish: date | None
    late_start: date | None
    late_finish: date | None
    total_float: int | None
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class GanttData(BaseModel):
    tasks: list[TaskResponse]
    critical_path: list[uuid.UUID]
    project_duration_days: int | None
