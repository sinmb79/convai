# CONAI — 건설 AI 통합관리 플랫폼

> **소형 건설업체의 잡무 70%를 없애는 AI 시스템**
>
> 현장소장을 대체하는 게 아닙니다. 현장소장이 직접 해야 할 판단은 그대로 두고,
> 매일 반복되는 행정 잡무만 AI가 처리합니다.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org)

---

## 이런 분께 필요합니다

- ✅ 작업일보를 매일 손으로 쓰고 있다
- ✅ 주간/월간 보고서 작성에 시간이 많이 걸린다
- ✅ 검측요청서를 처음부터 매번 만들어야 한다
- ✅ 날씨 때문에 공정이 꼬인 적이 있다
- ✅ 건설 법규·시방서를 빠르게 찾고 싶다

---

## 주요 기능 (Phase 1 MVP)

| 기능 | 설명 |
|---|---|
| 📋 **AI 작업일보** | 인원·작업내용 입력 → AI가 공식 일보 완성 |
| 🤖 **카카오 챗봇 연동** | 카카오톡으로 일보 입력, 법규 질문 |
| 📅 **Gantt 공정표** | WBS 기반 공정표, CPM 주공정선 자동 계산 |
| 🌤 **날씨 공정 경보** | 기상청 API 연동, 공종별 날씨 제약 자동 경보 |
| 🔬 **AI 검측요청서** | 공종 선택 → KCS 기반 체크리스트 자동 생성 |
| 📚 **법규 Q&A (RAG)** | 건설기술진흥법·산안법·KCS 시방서 즉시 검색 |
| 🏛 **인허가 체크리스트** | 공종별 인허가 목록, 진행상태 추적 |
| ⚙️ **커스텀 설정** | 발주처 프로파일, 공종 라이브러리, JSON 내보내기 |

---

## 시스템 구조

```
카카오톡 (입력 채널)
     ↓
CONAI Backend (FastAPI)
     ├── AI Engine (Claude API)
     ├── Core Engine (8개 모듈)
     │   ├── 공정관리 (WBS + Gantt + CPM)
     │   ├── 품질관리 (검측 + 품질시험)
     │   ├── 안전관리 (위험성 평가)
     │   ├── 공무·행정 (일보 + 보고서)
     │   ├── 날씨 연동 (기상청 API)
     │   ├── 인허가 관리
     │   ├── 측량 데이터
     │   └── 커스텀 설정
     └── Database (Supabase PostgreSQL + pgvector)
          ↑
CONAI Frontend (Next.js)  ← 웹 대시보드
```

---

## 빠른 시작 (5분 세팅)

### 1단계: 필요한 것 준비하기

먼저 아래 서비스에서 계정을 만들고 API 키를 발급받으세요:

| 서비스 | 용도 | 발급처 | 가격 |
|---|---|---|---|
| **Anthropic** | AI 핵심 (일보·보고서·Q&A) | [console.anthropic.com](https://console.anthropic.com) | 사용량 기반 |
| **Supabase** | 데이터베이스 | [supabase.com](https://supabase.com) | 무료 플랜 있음 |
| **Voyage AI** | 법규 검색 임베딩 | [voyageai.com](https://www.voyageai.com) | 무료 크레딧 있음 |
| **기상청 OpenAPI** | 날씨 예보 | [data.go.kr](https://www.data.go.kr) | **무료** |

> 💡 카카오 챗봇은 선택사항입니다. 없어도 웹으로 모든 기능을 사용할 수 있어요.

### 2단계: 코드 다운로드

```bash
git clone https://github.com/sinmb79/convai.git
cd convai
```

### 3단계: 환경변수 설정

```bash
# 백엔드 환경변수 파일 만들기
cp backend/.env.example backend/.env
```

`backend/.env` 파일을 메모장으로 열고, 아래 항목들을 실제 값으로 바꿔주세요:

```env
# 반드시 바꿔야 하는 항목들 ↓

# 데이터베이스 (Supabase에서 복사)
DATABASE_URL=postgresql+asyncpg://postgres:비밀번호@db.xxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=발급받은키
SUPABASE_SERVICE_KEY=발급받은서비스키

# AI (Anthropic에서 복사)
ANTHROPIC_API_KEY=sk-ant-...

# 날씨 (data.go.kr에서 복사, 무료)
KMA_API_KEY=발급받은키

# 법규 검색용 (Voyage AI에서 복사)
VOYAGE_API_KEY=pa-...

# 보안 키 (아무 랜덤 문자열로 바꿔주세요, 예: UUID)
SECRET_KEY=여기에-랜덤-문자열-입력
```

```bash
# 프론트엔드 환경변수 파일 만들기
cp frontend/.env.example frontend/.env.local
```

`frontend/.env.local` 파일:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4단계: 실행하기

**방법 A: Docker 사용 (추천)**

Docker Desktop이 설치되어 있다면:

```bash
docker compose up -d
```

잠시 기다린 후 DB 테이블을 만들어줍니다:

```bash
docker compose exec backend alembic upgrade head
```

**방법 B: 직접 실행**

터미널을 2개 열고:

```bash
# 터미널 1 - 백엔드
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
# 터미널 2 - 프론트엔드
cd frontend
npm install
npm run dev
```

### 5단계: 접속

| 주소 | 내용 |
|---|---|
| http://localhost:3000 | 웹 대시보드 |
| http://localhost:8000/docs | API 문서 (Swagger) |

첫 계정은 API를 통해 만들 수 있습니다:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@conai.app","password":"비밀번호","name":"홍길동","role":"admin"}'
```

---

## 법규 Q&A 기능 사용하기 (RAG 설정)

법규 Q&A 기능을 쓰려면, 법령·시방서 문서를 먼저 넣어야 합니다.

### 공개 자료 출처

| 자료 | 다운로드 |
|---|---|
| KCS 한국건설기준 | [kcsc.re.kr](https://www.kcsc.re.kr) |
| 건설기술진흥법 | [law.go.kr](https://www.law.go.kr) |
| 산업안전보건법 | [law.go.kr](https://www.law.go.kr) |
| 중대재해처벌법 | [law.go.kr](https://www.law.go.kr) |

> ⚠️ 법령 문서는 저작권 확인 후 사용하세요. 국가법령정보센터 자료는 공공누리 조건에 따라 활용 가능합니다.

### RAG 인덱싱 방법

Supabase에서 pgvector 확장을 활성화한 후:

```sql
-- Supabase SQL Editor에서 실행
CREATE EXTENSION IF NOT EXISTS vector;
```

문서 업로드는 API를 통해 이루어집니다 (업로드 기능은 다음 버전에 추가 예정).

---

## 카카오 챗봇 연동 (선택사항)

1. [Kakao i Open Builder](https://i.kakao.com) 접속
2. 새 챗봇 만들기
3. Skill 서버 URL: `https://내도메인/api/v1/kakao/webhook`
4. 챗봇을 카카오채널에 연결

카카오에서 보내는 메시지:
- `일보: 콘크리트 5명, 철근 3명 / 관로매설 50m 완료` → AI가 작업일보 생성
- `질문: 콘크리트 타설 최저기온은?` → 법규/시방서 검색 후 답변
- `날씨` → 현장 날씨 경보 확인

---

## 프로젝트 구조

```
convai/
├── backend/                  # Python FastAPI 서버
│   ├── app/
│   │   ├── api/              # REST API 엔드포인트
│   │   ├── models/           # 데이터베이스 모델
│   │   ├── schemas/          # 입출력 데이터 형식
│   │   ├── services/         # 핵심 비즈니스 로직
│   │   │   ├── ai_engine.py      # Claude AI 연동
│   │   │   ├── gantt.py          # CPM 공정 계산
│   │   │   ├── weather_service.py # 기상청 API
│   │   │   ├── rag_service.py     # 법규 검색
│   │   │   └── kakao_service.py  # 카카오 챗봇
│   │   └── core/             # 보안·DB·파일 저장
│   ├── alembic/              # DB 마이그레이션
│   └── tests/                # 단위 테스트
│
├── frontend/                 # Next.js 웹 대시보드
│   └── src/
│       ├── app/              # 페이지들
│       ├── components/       # UI 컴포넌트
│       ├── hooks/            # React 훅
│       └── lib/              # API 클라이언트·타입
│
├── docs/                     # 추가 문서
├── docker-compose.yml        # 로컬 개발 환경
└── README.md
```

---

## 기여하기

버그 신고, 기능 제안, 코드 기여 모두 환영합니다!

1. 이 저장소를 Fork
2. 새 브랜치 만들기: `git checkout -b feature/기능명`
3. 변경사항 커밋: `git commit -m "feat: 새 기능 추가"`
4. Push: `git push origin feature/기능명`
5. Pull Request 열기

---

## 오픈소스 범위

| 공개 (MIT) | 비공개 |
|---|---|
| Core Engine 구조 | 에이전트 페르소나·시나리오 |
| 공정관리·Gantt 로직 | 법령 DB (RAG 데이터) |
| 날씨 연동 엔진 | 발주처별 서식 템플릿 |
| 측량 수량 계산 | 인허가 자동 도출 DB |
| 카카오 챗봇 기본 구조 | Vision AI 모델 |

---

## 법적 고지

- AI가 생성한 작업일보·보고서는 **반드시 담당자가 검토·확인** 후 사용하세요
- 법규·시방서 Q&A는 **참고용**이며 법률 자문이 아닙니다
- 안전 관련 기능은 전문 안전관리자를 **대체하지 않습니다**
- 모든 AI 생성 문서의 최종 책임은 현장 책임자에게 있습니다

---

## 라이선스

이 프로젝트의 Core 부분은 [MIT License](LICENSE)로 배포됩니다.

---

## 만든 곳

**22B Labs / The 4th Path**
소형 건설업체의 디지털 전환을 돕습니다.

> "대형사가 12~22명으로 하는 일을 소형업체 1~2명이 AI와 함께 해낼 수 있도록"
