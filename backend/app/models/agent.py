import uuid
import enum
from sqlalchemy import String, Text, ForeignKey, Enum as SAEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class AgentType(str, enum.Enum):
    GONGSA = "gongsa"   # 공사 담당
    PUMJIL = "pumjil"   # 품질 담당
    ANJEON = "anjeon"   # 안전 담당
    GUMU   = "gumu"     # 공무 담당


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class AgentConversation(Base, UUIDMixin, TimestampMixin):
    """에이전트와의 대화 세션"""
    __tablename__ = "agent_conversations"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_id:    Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    agent_type: Mapped[AgentType] = mapped_column(SAEnum(AgentType, name="agent_type"), nullable=False)
    title:      Mapped[str | None] = mapped_column(String(200), nullable=True)
    status:     Mapped[ConversationStatus] = mapped_column(
        SAEnum(ConversationStatus, name="conversation_status"),
        default=ConversationStatus.ACTIVE,
        nullable=False,
    )

    # relationships
    project:  Mapped["Project"] = relationship("Project")
    user:     Mapped["User"]    = relationship("User")
    messages: Mapped[list["AgentMessage"]] = relationship(
        "AgentMessage", back_populates="conversation", cascade="all, delete-orphan",
        order_by="AgentMessage.created_at",
    )


class AgentMessage(Base, UUIDMixin, TimestampMixin):
    """에이전트 대화 메시지"""
    __tablename__ = "agent_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_conversations.id"), nullable=False
    )
    role:     Mapped[str] = mapped_column(String(20), nullable=False)   # user | assistant | system
    content:  Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # action proposals, references, etc.
    is_proactive: Mapped[bool] = mapped_column(Boolean, default=False)   # 에이전트가 먼저 보낸 메시지

    # relationships
    conversation: Mapped["AgentConversation"] = relationship("AgentConversation", back_populates="messages")


class GeofenceZone(Base, UUIDMixin, TimestampMixin):
    """익명 위험구역 Geofence"""
    __tablename__ = "geofence_zones"

    project_id:  Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name:        Mapped[str]       = mapped_column(String(100), nullable=False)   # "3공구 굴착면", "크레인 반경"
    zone_type:   Mapped[str]       = mapped_column(String(50), nullable=False)    # excavation, crane, confined_space
    coordinates: Mapped[list]      = mapped_column(JSONB, nullable=False)         # [[lat,lng], ...]
    radius_m:    Mapped[float | None] = mapped_column(nullable=True)              # 원형 구역용 반경(m)
    is_active:   Mapped[bool]      = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    project: Mapped["Project"] = relationship("Project")
