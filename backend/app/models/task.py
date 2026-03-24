import uuid
from sqlalchemy import String, Integer, Date, Boolean, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
import enum


class DependencyType(str, enum.Enum):
    FS = "FS"  # Finish-to-Start
    SS = "SS"  # Start-to-Start
    FF = "FF"  # Finish-to-Finish
    SF = "SF"  # Start-to-Finish


class Task(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tasks"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    wbs_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wbs_items.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    planned_start: Mapped[str | None] = mapped_column(Date, nullable=True)
    planned_end: Mapped[str | None] = mapped_column(Date, nullable=True)
    actual_start: Mapped[str | None] = mapped_column(Date, nullable=True)
    actual_end: Mapped[str | None] = mapped_column(Date, nullable=True)
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_milestone: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    early_start: Mapped[str | None] = mapped_column(Date, nullable=True)  # CPM
    early_finish: Mapped[str | None] = mapped_column(Date, nullable=True)
    late_start: Mapped[str | None] = mapped_column(Date, nullable=True)
    late_finish: Mapped[str | None] = mapped_column(Date, nullable=True)
    total_float: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    wbs_item: Mapped["WBSItem | None"] = relationship("WBSItem", back_populates="tasks")
    predecessors: Mapped[list["TaskDependency"]] = relationship(
        "TaskDependency", foreign_keys="TaskDependency.successor_id", back_populates="successor"
    )
    successors: Mapped[list["TaskDependency"]] = relationship(
        "TaskDependency", foreign_keys="TaskDependency.predecessor_id", back_populates="predecessor"
    )
    weather_alerts: Mapped[list["WeatherAlert"]] = relationship("WeatherAlert", back_populates="task")


class TaskDependency(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "task_dependencies"

    predecessor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    successor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    dependency_type: Mapped[DependencyType] = mapped_column(
        SAEnum(DependencyType, name="dependency_type"), default=DependencyType.FS, nullable=False
    )
    lag_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # relationships
    predecessor: Mapped["Task"] = relationship("Task", foreign_keys=[predecessor_id], back_populates="successors")
    successor: Mapped["Task"] = relationship("Task", foreign_keys=[successor_id], back_populates="predecessors")
