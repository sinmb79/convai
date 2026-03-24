import uuid
from sqlalchemy import String, Integer, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
import enum


class RagSourceType(str, enum.Enum):
    KCS = "kcs"
    LAW = "law"
    REGULATION = "regulation"
    GUIDELINE = "guideline"


class RagSource(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "rag_sources"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    source_type: Mapped[RagSourceType] = mapped_column(
        SAEnum(RagSourceType, name="rag_source_type"), nullable=False
    )
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_s3_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # relationships
    chunks: Mapped[list["RagChunk"]] = relationship("RagChunk", back_populates="source", cascade="all, delete-orphan")


class RagChunk(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "rag_chunks"

    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rag_sources.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Note: embedding column (VECTOR) added via Alembic migration with pgvector extension
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # relationships
    source: Mapped["RagSource"] = relationship("RagSource", back_populates="chunks")
