import uuid
from datetime import date, datetime
from pydantic import BaseModel
from app.models.weather import ForecastType, AlertSeverity


class WeatherDataResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    forecast_date: date
    forecast_type: ForecastType
    temperature_high: float | None
    temperature_low: float | None
    precipitation_mm: float | None
    wind_speed_ms: float | None
    weather_code: str | None
    fetched_at: datetime

    model_config = {"from_attributes": True}


class WeatherAlertResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    task_id: uuid.UUID | None
    alert_date: date
    alert_type: str
    severity: AlertSeverity
    message: str
    is_acknowledged: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WeatherForecastSummary(BaseModel):
    forecast: list[WeatherDataResponse]
    active_alerts: list[WeatherAlertResponse]
