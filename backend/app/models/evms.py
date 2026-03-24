import uuid
from datetime import date
from sqlalchemy import Date, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class EVMSSnapshot(Base, UUIDMixin, TimestampMixin):
    """
    EVMS 공정 성과 스냅샷 (기준일 기준 PV/EV/AC 저장)

    PV (Planned Value)  = 계획 공정률 기준 예산 투입액
    EV (Earned Value)   = 실제 완료 공정률 기준 예산 투입액
    AC (Actual Cost)    = 실제 투입 비용
    SPI = EV / PV       (1 이상: 공정 앞서감, 미만: 지연)
    CPI = EV / AC       (1 이상: 비용 효율적, 미만: 비용 초과)
    """
    __tablename__ = "evms_snapshots"

    project_id:       Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    snapshot_date:    Mapped[date]      = mapped_column(Date, nullable=False, index=True)

    # 예산 (원)
    total_budget:     Mapped[float | None] = mapped_column(Float, nullable=True)

    # 공정률 (%)
    planned_progress: Mapped[float | None] = mapped_column(Float, nullable=True)   # 계획 공정률
    actual_progress:  Mapped[float | None] = mapped_column(Float, nullable=True)   # 실제 공정률

    # EVM 핵심 지표 (원)
    pv: Mapped[float | None] = mapped_column(Float, nullable=True)   # Planned Value
    ev: Mapped[float | None] = mapped_column(Float, nullable=True)   # Earned Value
    ac: Mapped[float | None] = mapped_column(Float, nullable=True)   # Actual Cost

    # 파생 지수
    spi: Mapped[float | None] = mapped_column(Float, nullable=True)  # Schedule Performance Index
    cpi: Mapped[float | None] = mapped_column(Float, nullable=True)  # Cost Performance Index

    # 예측
    eac: Mapped[float | None] = mapped_column(Float, nullable=True)  # Estimate at Completion
    etc: Mapped[float | None] = mapped_column(Float, nullable=True)  # Estimate to Complete

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # WBS별 세부 내역

    # relationships
    project: Mapped["Project"] = relationship("Project")
