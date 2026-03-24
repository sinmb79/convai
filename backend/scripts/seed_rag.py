"""
RAG 시드 스크립트
법규/시방서 PDF 또는 텍스트 파일을 pgvector에 색인합니다.

사용법:
  python scripts/seed_rag.py --file "경로/파일명.pdf" --title "KCS 14 20 10" --type kcs
  python scripts/seed_rag.py --file "경로/파일명.txt" --title "건설안전관리법" --type law
  python scripts/seed_rag.py --list   # 색인된 소스 목록 출력
  python scripts/seed_rag.py --delete <source_id>  # 소스 및 청크 삭제

지원 파일 형식: PDF, TXT, MD
"""
import argparse
import asyncio
import os
import sys
import uuid
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from sqlalchemy import select, text, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models.rag import RagSource, RagChunk, RagSourceType

# ─── 텍스트 추출 ────────────────────────────────────────────────────────────────

def extract_text_from_pdf(filepath: str) -> str:
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        return "\n".join(text_parts)
    except ImportError:
        # fallback: pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(filepath)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            raise RuntimeError(
                "PDF 읽기 라이브러리가 없습니다.\n"
                "설치: pip install pdfplumber  또는  pip install pypdf"
            )


def extract_text(filepath: str) -> str:
    ext = Path(filepath).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(filepath)
    elif ext in (".txt", ".md"):
        with open(filepath, encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"지원하지 않는 파일 형식: {ext}  (pdf, txt, md만 가능)")


# ─── 텍스트 청킹 ────────────────────────────────────────────────────────────────

def split_chunks(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """
    단락 단위로 먼저 분리하고, chunk_size 초과 시 슬라이딩 윈도우로 분할.
    overlap: 앞 청크 마지막 n 글자를 다음 청크 앞에 붙임 (문맥 유지).
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) < chunk_size:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            # 긴 단락은 슬라이딩 윈도우
            if len(para) > chunk_size:
                for start in range(0, len(para), chunk_size - overlap):
                    chunks.append(para[start : start + chunk_size])
            else:
                current = para

    if current:
        chunks.append(current)

    return [c for c in chunks if len(c) > 50]  # 너무 짧은 청크 제거


# ─── 임베딩 ─────────────────────────────────────────────────────────────────────

async def embed_batch(texts: list[str]) -> list[list[float]]:
    """배치 임베딩 (Voyage AI 또는 OpenAI)"""
    if settings.VOYAGE_API_KEY:
        return await _embed_voyage_batch(texts)
    elif settings.OPENAI_API_KEY:
        return await _embed_openai_batch(texts)
    else:
        raise ValueError("VOYAGE_API_KEY 또는 OPENAI_API_KEY를 .env에 설정하세요.")


async def _embed_voyage_batch(texts: list[str]) -> list[list[float]]:
    # Voyage AI는 배치 최대 128개
    BATCH = 128
    results = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i in range(0, len(texts), BATCH):
            batch = texts[i : i + BATCH]
            resp = await client.post(
                "https://api.voyageai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {settings.VOYAGE_API_KEY}"},
                json={"model": settings.EMBEDDING_MODEL, "input": batch},
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            results.extend(item["embedding"] for item in sorted(data, key=lambda x: x["index"]))
    return results


async def _embed_openai_batch(texts: list[str]) -> list[list[float]]:
    BATCH = 100
    results = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i in range(0, len(texts), BATCH):
            batch = texts[i : i + BATCH]
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={"model": "text-embedding-3-small", "input": batch},
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            results.extend(item["embedding"] for item in sorted(data, key=lambda x: x["index"]))
    return results


# ─── DB 작업 ─────────────────────────────────────────────────────────────────────

async def get_session() -> AsyncSession:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    return factory()


async def seed(filepath: str, title: str, source_type: str, chunk_size: int, overlap: int):
    print(f"\n[1/4] 파일 읽기: {filepath}")
    raw_text = extract_text(filepath)
    print(f"      추출된 텍스트: {len(raw_text):,}자")

    print(f"[2/4] 청크 분할 (크기={chunk_size}, 겹침={overlap})")
    chunks = split_chunks(raw_text, chunk_size, overlap)
    print(f"      청크 수: {len(chunks)}개")

    print(f"[3/4] 임베딩 생성 중...")
    embeddings = await embed_batch([c for c in chunks])
    print(f"      임베딩 완료: {len(embeddings)}개")

    print(f"[4/4] DB 저장 중...")
    async with await get_session() as session:
        # RagSource 생성
        source = RagSource(
            title=title,
            source_type=RagSourceType(source_type),
        )
        session.add(source)
        await session.flush()  # source.id 확보

        # RagChunk 배치 저장
        dim = settings.EMBEDDING_DIMENSIONS
        for idx, (content, emb) in enumerate(zip(chunks, embeddings)):
            chunk = RagChunk(
                source_id=source.id,
                chunk_index=idx,
                content=content,
                metadata_={"chunk_index": idx, "source_title": title},
            )
            session.add(chunk)
            await session.flush()  # chunk.id 확보

            # pgvector 직접 업데이트 (SQLAlchemy ORM이 VECTOR 타입을 직접 지원 안 함)
            emb_str = "[" + ",".join(str(x) for x in emb) + "]"
            await session.execute(
                text("UPDATE rag_chunks SET embedding = :emb WHERE id = :id"),
                {"emb": emb_str, "id": chunk.id},
            )

        await session.commit()
        print(f"\n완료! source_id={source.id}")
        print(f"  제목: {title}")
        print(f"  타입: {source_type}")
        print(f"  청크: {len(chunks)}개 저장됨")


async def list_sources():
    async with await get_session() as session:
        result = await session.execute(
            select(RagSource).order_by(RagSource.created_at.desc())
        )
        sources = result.scalars().all()
        if not sources:
            print("색인된 소스가 없습니다.")
            return
        print(f"\n{'ID':<38} {'타입':<12} {'제목'}")
        print("-" * 80)
        for s in sources:
            chunks_q = await session.execute(
                text("SELECT COUNT(*) FROM rag_chunks WHERE source_id = :id"),
                {"id": s.id},
            )
            count = chunks_q.scalar()
            print(f"{str(s.id):<38} {s.source_type.value:<12} {s.title}  ({count}청크)")


async def delete_source(source_id: str):
    async with await get_session() as session:
        sid = uuid.UUID(source_id)
        result = await session.execute(select(RagSource).where(RagSource.id == sid))
        source = result.scalar_one_or_none()
        if not source:
            print(f"소스를 찾을 수 없습니다: {source_id}")
            return
        await session.execute(delete(RagChunk).where(RagChunk.source_id == sid))
        await session.delete(source)
        await session.commit()
        print(f"삭제 완료: {source.title} ({source_id})")


# ─── CLI ─────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CONAI RAG 시드 스크립트 — 법규/시방서를 pgvector에 색인",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--file", help="임베딩할 파일 경로 (pdf/txt/md)")
    parser.add_argument("--title", help="문서 제목 (예: KCS 14 20 10 콘크리트 시방서)")
    parser.add_argument(
        "--type",
        choices=["kcs", "law", "regulation", "guideline"],
        default="kcs",
        help="소스 타입: kcs(시방서), law(법령), regulation(규정), guideline(지침)",
    )
    parser.add_argument("--chunk-size", type=int, default=800, help="청크 최대 글자 수 (기본: 800)")
    parser.add_argument("--overlap", type=int, default=100, help="청크 겹침 글자 수 (기본: 100)")
    parser.add_argument("--list", action="store_true", help="색인된 소스 목록 출력")
    parser.add_argument("--delete", metavar="SOURCE_ID", help="소스 ID로 삭제")

    args = parser.parse_args()

    if args.list:
        asyncio.run(list_sources())
    elif args.delete:
        asyncio.run(delete_source(args.delete))
    elif args.file:
        if not args.title:
            parser.error("--title 이 필요합니다")
        if not os.path.exists(args.file):
            print(f"파일을 찾을 수 없습니다: {args.file}")
            sys.exit(1)
        asyncio.run(seed(args.file, args.title, args.type, args.chunk_size, args.overlap))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
