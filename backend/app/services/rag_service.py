"""
RAG (Retrieval-Augmented Generation) service.
Embeds questions, retrieves relevant chunks, and generates answers with Claude.
"""
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.config import settings
from app.models.rag import RagChunk, RagSource
from app.services.ai_engine import complete
from app.services.prompts.rag import SYSTEM_PROMPT, build_prompt


async def embed_text(text_input: str) -> list[float]:
    """Get embedding vector for text using Voyage AI or OpenAI."""
    if settings.VOYAGE_API_KEY:
        return await _embed_voyage(text_input)
    elif settings.OPENAI_API_KEY:
        return await _embed_openai(text_input)
    else:
        raise ValueError("임베딩 API 키가 설정되지 않았습니다 (VOYAGE_API_KEY 또는 OPENAI_API_KEY)")


async def _embed_voyage(text_input: str) -> list[float]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.voyageai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.VOYAGE_API_KEY}"},
            json={"model": settings.EMBEDDING_MODEL, "input": text_input},
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]


async def _embed_openai(text_input: str) -> list[float]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={"model": "text-embedding-3-small", "input": text_input},
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]


async def retrieve_chunks(
    db: AsyncSession,
    question_embedding: list[float],
    top_k: int = 5,
    source_types: list[str] | None = None,
) -> list[dict]:
    """Retrieve most relevant chunks using pgvector cosine similarity."""
    embedding_str = "[" + ",".join(str(x) for x in question_embedding) + "]"

    # Build query with optional source type filter
    source_filter = ""
    if source_types:
        types_str = ", ".join(f"'{t}'" for t in source_types)
        source_filter = f"AND rs.source_type IN ({types_str})"

    query = text(f"""
        SELECT
            rc.id,
            rc.content,
            rc.metadata,
            rs.title,
            rs.source_type,
            1 - (rc.embedding <=> '{embedding_str}'::vector) AS relevance_score
        FROM rag_chunks rc
        JOIN rag_sources rs ON rs.id = rc.source_id
        WHERE rc.embedding IS NOT NULL
        {source_filter}
        ORDER BY rc.embedding <=> '{embedding_str}'::vector
        LIMIT {top_k}
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    return [
        {
            "id": str(row.id),
            "content": row.content,
            "metadata": row.metadata,
            "title": row.title,
            "source_type": row.source_type,
            "relevance_score": float(row.relevance_score),
        }
        for row in rows
    ]


async def ask(
    db: AsyncSession,
    question: str,
    top_k: int = 5,
    source_types: list[str] | None = None,
) -> dict:
    """Full RAG pipeline: embed -> retrieve -> generate."""
    # 1. Embed the question
    embedding = await embed_text(question)

    # 2. Retrieve relevant chunks
    chunks = await retrieve_chunks(db, embedding, top_k, source_types)

    if not chunks:
        return {
            "question": question,
            "answer": "관련 자료를 찾을 수 없습니다. 더 구체적인 질문을 입력하거나, 관련 자료가 업로드되었는지 확인해주세요.",
            "sources": [],
        }

    # 3. Build prompt and generate answer
    prompt = build_prompt(question, chunks)
    answer = await complete(
        messages=[{"role": "user", "content": prompt}],
        system=SYSTEM_PROMPT,
        temperature=0.5,
    )

    return {
        "question": question,
        "answer": answer,
        "sources": chunks,
    }
