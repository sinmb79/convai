import uuid
from datetime import date
from pydantic import BaseModel, model_validator
from app.models.quality import QualityResult


class QualityTestCreate(BaseModel):
    wbs_item_id: uuid.UUID | None = None
    test_type: str  # compression_strength, slump, compaction, etc.
    test_date: date
    location_detail: str | None = None
    design_value: float | None = None
    measured_value: float
    unit: str
    result: QualityResult | None = None  # auto-calculated if design_value provided
    lab_name: str | None = None
    report_number: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def auto_result(self) -> "QualityTestCreate":
        if self.result is None:
            if self.design_value is not None:
                self.result = QualityResult.PASS if self.measured_value >= self.design_value else QualityResult.FAIL
            else:
                self.result = QualityResult.PASS
        return self


class QualityTestUpdate(BaseModel):
    test_date: date | None = None
    location_detail: str | None = None
    design_value: float | None = None
    measured_value: float | None = None
    unit: str | None = None
    result: QualityResult | None = None
    lab_name: str | None = None
    report_number: str | None = None
    notes: str | None = None


class QualityTestResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    wbs_item_id: uuid.UUID | None
    test_type: str
    test_date: date
    location_detail: str | None
    design_value: float | None
    measured_value: float
    unit: str
    result: QualityResult
    lab_name: str | None
    report_number: str | None
    notes: str | None

    model_config = {"from_attributes": True}
