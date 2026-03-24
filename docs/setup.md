# CONAI 개발 환경 설정 가이드

## 빠른 시작 (Docker)

```bash
# 1. 환경변수 설정
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
# .env 파일에 API 키 입력

# 2. Docker Compose 실행
docker compose up -d

# 3. DB 마이그레이션
docker compose exec backend alembic upgrade head

# 4. 접속
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 로컬 개발 (Docker 없이)

### 사전 요구사항
- Python 3.11+
- Node.js 20+
- PostgreSQL 16+ (pgvector 확장 포함)

### Backend

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# 의존성 설치
pip install -e .

# 환경변수 설정
cp .env.example .env
# .env 파일에서 DATABASE_URL, ANTHROPIC_API_KEY 등 설정

# DB 마이그레이션
alembic upgrade head

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# 의존성 설치
npm install

# 환경변수 설정
cp .env.example .env.local

# 개발 서버 실행
npm run dev
```

## 필수 API 키

| 서비스 | 용도 | 발급처 |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude AI (일보·보고서·RAG) | console.anthropic.com |
| `KMA_API_KEY` | 날씨 예보 (기상청) | data.go.kr |
| `VOYAGE_API_KEY` 또는 `OPENAI_API_KEY` | RAG 임베딩 | voyageai.com / openai.com |
| `SUPABASE_*` | DB·스토리지 | supabase.com |

## RAG 시드 데이터 준비

법규/시방서 문서를 pgvector에 색인하려면:

```bash
cd backend

# 1. 문서 파일 준비 (PDF 또는 텍스트)
# 예: KCS 14 20 10 콘크리트 시방서.pdf

# 2. 시드 스크립트 실행 (개발 예정)
python scripts/seed_rag.py --file "경로/파일명.pdf" --title "KCS 14 20 10" --type kcs
```

## 카카오 챗봇 연동

1. [Kakao i Open Builder](https://i.kakao.com) 에서 챗봇 생성
2. Skill API URL: `https://your-domain.com/api/v1/kakao/webhook`
3. 카카오 개발자센터에서 App Key 발급 후 `.env`에 설정

## 테스트

```bash
# Backend 테스트
cd backend
pytest

# Frontend 타입 체크
cd frontend
npm run type-check
```
