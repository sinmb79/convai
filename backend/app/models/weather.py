import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Date, Float, Integer, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
import enum


class ForecastType(str, enum.Enum):
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    OBSERVED = "observed"


class AlertSeverity(str, enum.Enum):
    WARNING = "warning"
    CRITICAL = "critical"


class WeatherData(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "weather_data"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    forecast_date: Mapped[str] = mapped_column(Date, nullable=False)
    forecast_type: Mapped[ForecastType] = mapped_column(
        SAEnum(ForecastType, name="forecast_type"), nullable=False
    )
    temperature_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    precipitation_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(nullable=False)

    # relationships
    project: Mapped["Project"] = relationship("Project", back_populates="weather_data")


class WeatherAlert(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "weather_alerts"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    alert_date: Mapped[str] = mapped_column(Date, nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)  # rain_concrete, wind_highwork, etc.
    severity: Mapped[AlertSeverity] = mapped_column(
        SAEnum(AlertSeverity, name="alert_severity"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # relationships
    project: Mapped["Project"] = relationship("Project", back_populates="weather_alerts")
    task: Mapped["Task | None"] = relationship("Task", back_populates="weather_alerts")
