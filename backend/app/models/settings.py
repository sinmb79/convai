import uuid
from sqlalchemy import String, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class ClientProfile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "client_profiles"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    report_frequency: Mapped[str] = mapped_column(String(20), default="weekly", nullable=False)
    template_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    contact_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # relationships
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="client_profile")


class AlertRule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "alert_rules"

    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    condition: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    channels: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    recipients: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WorkTypeLibrary(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "work_type_library"

    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    weather_constraints: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    default_checklist: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
