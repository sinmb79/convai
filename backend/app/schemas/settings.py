import uuid
from datetime import datetime
from pydantic import BaseModel


class ClientProfileCreate(BaseModel):
    name: str
    report_frequency: str = "weekly"
    template_config: dict | None = None
    contact_info: dict | None = None
    is_default: bool = False


class ClientProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    report_frequency: str
    template_config: dict | None
    contact_info: dict | None
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkTypeCreate(BaseModel):
    code: str
    name: str
    category: str
    weather_constraints: dict | None = None
    default_checklist: list | None = None


class WorkTypeResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    category: str
    weather_constraints: dict | None
    default_checklist: list | None
    is_system: bool

    model_config = {"from_attributes": True}


class AlertRuleCreate(BaseModel):
    project_id: uuid.UUID | None = None
    rule_name: str
    condition: dict | None = None
    channels: list | None = None
    recipients: list | None = None
    is_active: bool = True


class AlertRuleResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID | None
    rule_name: str
    condition: dict | None
    channels: list | None
    recipients: list | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SettingsExport(BaseModel):
    version: str = "1.0"
    client_profiles: list[ClientProfileResponse]
    work_types: list[WorkTypeResponse]
    alert_rules: list[AlertRuleResponse]
    exported_at: datetime
