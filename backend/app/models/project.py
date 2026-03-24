import uuid
from sqlalchemy import String, Integer, BigInteger, Date, Float, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
import enum


class ProjectStatus(str, enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"


class ConstructionType(str, enum.Enum):
    ROAD = "road"
    SEWER = "sewer"
    WATER = "water"
    BRIDGE = "bridge"
    SITE_WORK = "site_work"
    OTHER = "other"


class Project(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    client_profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("client_profiles.id"), nullable=True)
    construction_type: Mapped[ConstructionType] = mapped_column(
        SAEnum(ConstructionType, name="construction_type"), default=ConstructionType.OTHER, nullable=False
    )
    contract_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    start_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    location_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather_grid_x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weather_grid_y: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus, name="project_status"), default=ProjectStatus.PLANNING, nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # relationships
    owner: Mapped["User"] = relationship("User", back_populates="owned_projects", foreign_keys=[owner_id])
    wbs_items: Mapped[list["WBSItem"]] = relationship("WBSItem", back_populates="project", cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    daily_reports: Mapped[list["DailyReport"]] = relationship("DailyReport", back_populates="project", cascade="all, delete-orphan")
    inspection_requests: Mapped[list["InspectionRequest"]] = relationship("InspectionRequest", back_populates="project", cascade="all, delete-orphan")
    quality_tests: Mapped[list["QualityTest"]] = relationship("QualityTest", back_populates="project", cascade="all, delete-orphan")
    weather_data: Mapped[list["WeatherData"]] = relationship("WeatherData", back_populates="project", cascade="all, delete-orphan")
    weather_alerts: Mapped[list["WeatherAlert"]] = relationship("WeatherAlert", back_populates="project", cascade="all, delete-orphan")
    permit_items: Mapped[list["PermitItem"]] = relationship("PermitItem", back_populates="project", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="project", cascade="all, delete-orphan")
    client_profile: Mapped["ClientProfile | None"] = relationship("ClientProfile", back_populates="projects")


class WBSItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "wbs_items"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wbs_items.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    design_qty: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # relationships
    project: Mapped["Project"] = relationship("Project", back_populates="wbs_items")
    parent: Mapped["WBSItem | None"] = relationship("WBSItem", remote_side="WBSItem.id", back_populates="children")
    children: Mapped[list["WBSItem"]] = relationship("WBSItem", back_populates="parent")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="wbs_item")
