import uuid
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from sqlalchemy import select, func
from app.deps import CurrentUser, DB
from app.models.rag import RagSource, RagChunk
from app.schemas.rag import RagAskRequest, RagAskResponse, RagSourceCreate, RagSourceResponse, RagSource as RagSourceSchema
from app.services.rag_service import ask

router = APIRouter(prefix="/rag", tags=["법규/시방서 Q&A (RAG)"])


@router.post("/ask", response_model=RagAskResponse)
async def ask_question(data: RagAskRequest, db: DB, current_user: CurrentUser):
    """Ask a question about construction laws and specifications."""
    source_types = [st.value for st in data.source_types] if data.source_types else None
    result = await ask(db, data.question, data.top_k, source_types)

    sources = [
        RagSourceSchema(
            id=uuid.UUID(s["id"]),
            title=s["title"],
            source_type=s["source_type"],
            chunk_content=s["content"][:500],  # Truncate for response
            relevance_score=s["relevance_score"],
        )
        for s in result.get("sources", [])
    ]

    return RagAskResponse(
        question=result["question"],
        answer=result["answer"],
        sources=sources,
    )


@router.get("/sources", response_model=list[RagSourceResponse])
async def list_sources(db: DB, current_user: CurrentUser):
    """List all indexed RAG sources with chunk counts."""
    result = await db.execute(
        select(RagSource, func.count(RagChunk.id).label("chunk_count"))
        .outerjoin(RagChunk, RagChunk.source_id == RagSource.id)
        .group_by(RagSource.id)
        .order_by(RagSource.created_at.desc())
    )
    rows = result.fetchall()
    return [
        RagSourceResponse(
            id=row.RagSource.id,
            title=row.RagSource.title,
            source_type=row.RagSource.source_type,
            source_url=row.RagSource.source_url,
            chunk_count=row.chunk_count,
            created_at=row.RagSource.created_at,
        )
        for row in rows
    ]


@router.post("/sources", response_model=RagSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(data: RagSourceCreate, db: DB, current_user: CurrentUser):
    """Register a new RAG source (metadata only; content indexed separately)."""
    source = RagSource(**data.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return RagSourceResponse(
        id=source.id,
        title=source.title,
        source_type=source.source_type,
        source_url=source.source_url,
        chunk_count=0,
        created_at=source.created_at,
    )
