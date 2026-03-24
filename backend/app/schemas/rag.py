import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.rag import RagSourceType


class RagAskRequest(BaseModel):
    question: str
    source_types: list[RagSourceType] | None = None  # Filter by source type
    top_k: int = 5


class RagSource(BaseModel):
    id: uuid.UUID
    title: str
    source_type: RagSourceType
    chunk_content: str
    relevance_score: float

    model_config = {"from_attributes": True}


class RagAskResponse(BaseModel):
    question: str
    answer: str
    sources: list[RagSource]
    disclaimer: str = "이 답변은 참고용이며 법률 자문이 아닙니다. 중요 사항은 전문가에게 확인하세요."


class RagSourceCreate(BaseModel):
    title: str
    source_type: RagSourceType
    source_url: str | None = None


class RagSourceResponse(BaseModel):
    id: uuid.UUID
    title: str
    source_type: RagSourceType
    source_url: str | None
    chunk_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}
