# CONAI — 건설 AI 통합관리 플랫폼

> **소형 건설업체의 잡무 70%를 없애는 AI 시스템**
>
> 현장소장이 직접 해야 할 판단은 그대로 두고,
> 매일 반복되는 행정 잡무·문서 작업·안전 관리를 AI가 처리합니다.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org)
[![Claude AI](https://img.shields.io/badge/Claude-Sonnet-orange.svg)](https://anthropic.com)

---

## 이런 분께 필요합니다

- ✅ 작업일보를 매일 손으로 쓰고 있다
- ✅ 주간·월간 보고서 작성에 시간이 많이 걸린다
- ✅ 검측요청서를 처음부터 매번 만들어야 한다
- ✅ 날씨 때문에 공정이 꼬인 적이 있다
- ✅ 건설 법규·시방서를 빠르게 찾고 싶다
- ✅ 안전 TBM 자료를 매일 새로 만들기 번거롭다
- ✅ 발주처에게 공사 현황을 실시간으로 보여주고 싶다
- ✅ 준공도서 패키지를 한 번에 뽑고 싶다

---

## 전체 기능 구성

CONAI는 3단계(Phase)로 구성됩니다. **현재 Phase 1~3 모두 구현 완료** 상태입니다.

### Phase 1 — 기본 업무 자동화

| 기능 | 설명 |
|---|---|
| 📋 **AI 작업일보** | 인원·작업내용 입력 → AI가 공식 일보 완성, PDF 출력 |
| 📅 **Gantt 공정표** | WBS 기반 공정표, CPM 주공정선 자동 계산 |
| 🌤 **날씨 공정 경보** | 기상청 API 연동, 공종별 날씨 제약 자동 경보 |
| 🔬 **AI 검측요청서** | 공종 선택 → KCS 기반 체크리스트 자동 생성, PDF 출력 |
| 📄 **공정보고서** | 주간·월간 보고서 AI 초안 생성, PDF 출력 |
| 🧪 **품질시험 관리** | 시험 기록, 합격/불합격 자동 판정, 합격률 통계 |
| 📚 **법규 Q&A (RAG)** | 건설기술진흥법·산안법·KCS 시방서 즉시 검색 |
| 🏛 **인허가 체크리스트** | 공종 입력 → AI가 필요 인허가 자동 도출 |
| 🤖 **카카오 챗봇** | 카카오톡으로 일보 입력, 법규 질문 |
| ⚙️ **커스텀 설정** | 발주처 프로파일, 공종 라이브러리, JSON 내보내기 |

### Phase 2 — AI 에이전트 4인방

각 에이전트는 독립된 역할을 가진 Claude AI 인스턴스입니다. **에이전트는 제안하고, 현장소장이 결정합니다.**

| 에이전트 | 역할 | 주요 기능 |
|---|---|---|
| 🏗 **GONGSA** (공사) | 공정 관리 | 매일 07:00 자동 브리핑, 공기 지연 감지, 날씨 연동 작업 조정 제안 |
| 🔬 **PUMJIL** (품질) | 품질 관리 | 시공 전 체크리스트 자동 발송, 사진 1차 판독, 시험 기한 추적 |
| 🦺 **ANJEON** (안전) | 안전 관리 | 위험 공정 사전 경보, TBM 자동 생성, 중대재해처벌법 Q&A |
| 📝 **GUMU** (공무) | 행정 관리 | 인허가 능동 추적, 기성청구 제안, 주간 보고서 초안 |

**에이전트 협업 시나리오** — 여러 에이전트가 하나의 상황을 함께 처리합니다:
- `concrete_pour`: 콘크리트 타설 당일 (GONGSA → PUMJIL → ANJEON)
- `excavation`: 굴착 작업 당일 (GONGSA → ANJEON → PUMJIL)
- `weekly_report`: 주간 보고 (GONGSA → PUMJIL → GUMU)

**Phase 2 추가 기능:**

| 기능 | 설명 |
|---|---|
| 📊 **EVMS** | 공정 성과 지수 자동 계산 (PV·EV·AC·SPI·CPI) |
| 📸 **Vision AI L1** | 현장 사진 자동 분류, 공종·위치 태깅, 일보 자동 첨부 |
| 👷 **Vision AI L2** | 안전모·안전조끼 착용 감지 (AI 1차 분석, 최종 판정은 책임자) |
| 📍 **위험구역 Geofence** | 굴착면·크레인 반경 등 위험구역 설정, 진입 감지 경보 (익명) |

### Phase 3 — 완전 자동화

| 기능 | 설명 |
|---|---|
| 📈 **EVMS 완전 자동화** | 매일 자정 스냅샷 자동 생성, 공기 지연 AI 예측, 기성청구 금액 자동 산출 |
| 🌅 **아침 브리핑 자동화** | 매일 07:00 GONGSA가 공정 브리핑 자동 생성 |
| 📦 **준공도서 패키지** | 작업일보·품질시험·검측이력·인허가 → PDF 번들 ZIP 자동 생성 |
| 🔍 **Vision AI L3** | 설계 도면 vs 현장 사진 비교 판독 (철근 배근, 거푸집 치수) |
| 📐 **설계도서 파싱** | 도면 이미지/텍스트에서 공종·수량·규격 자동 추출 |
| 📄 **HWP 출력** | 보고서·일보를 한글(HWP) 형식으로 내보내기 (Pandoc 필요) |
| 🏢 **발주처 전용 포털** | 토큰 기반 읽기 전용 URL — 발주처가 공사 현황을 실시간 확인 |

---

## 시스템 구조

```
[현장소장]
    │
    ├── 카카오톡 ──────────────────────────────┐
    │                                          ↓
    └── 웹 대시보드 (Next.js) ──── CONAI Backend (FastAPI)
                                        │
                            ┌───────────┼───────────────────┐
                            │           │                   │
                       AI Engine    Core Engine          DB
                      (Claude)     8개 업무 모듈    (Supabase
                            │                      PostgreSQL
                     AI 에이전트                    + pgvector)
                    GONGSA / PUMJIL
                    ANJEON / GUMU
```

---

## 빠른 시작 (5분 세팅)

### 1단계: 필요한 것 준비하기

아래 서비스에서 API 키를 발급받으세요. (**★ 표시가 없으면 선택사항입니다**)

| 서비스 | 용도 | 발급처 | 가격 |
|---|---|---|---|
| ★ **Anthropic** | AI 핵심 (일보·에이전트·Q&A) | [console.anthropic.com](https://console.anthropic.com) | 사용량 기반 |
| ★ **Supabase** | 데이터베이스 | [supabase.com](https://supabase.com) | **무료** 플랜 있음 |
| ★ **기상청 OpenAPI** | 날씨 예보 | [data.go.kr](https://www.data.go.kr) | **완전 무료** |
| **Voyage AI** | 법규 검색 (RAG) | [voyageai.com](https://www.voyageai.com) | 무료 크레딧 있음 |
| **카카오** | 챗봇 입력 채널 | [i.kakao.com](https://i.kakao.com) | **무료** |

> 💡 카카오 챗봇 없이도 웹 대시보드로 모든 기능을 사용할 수 있습니다.

> 💡 법규 Q&A를 사용하지 않는다면 Voyage AI 키가 없어도 됩니다.

### 2단계: 코드 다운로드

```bash
git clone https://github.com/sinmb79/convai.git
cd convai
```

### 3단계: 환경변수 설정

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

`backend/.env` 파일을 열고 실제 값으로 바꿔주세요:

```
SECRET_KEY=아무-랜덤-문자열-32자-이상
DATABASE_URL=Supabase에서-복사한-주소
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=발급받은-키
SUPABASE_SERVICE_KEY=발급받은-서비스키
ANTHROPIC_API_KEY=sk-ant-...
KMA_API_KEY=기상청에서-발급받은-키
VOYAGE_API_KEY=pa-...  (RAG 사용 시)
```

`frontend/.env.local` 파일:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> 💡 SECRET_KEY는 아래 명령으로 만들 수 있습니다:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### 4단계: 실행하기

**방법 A: Docker 사용 (가장 쉬운 방법, 추천)**

[Docker Desktop](https://www.docker.com/products/docker-desktop/) 설치 후:

```bash
# 전체 실행 (DB + 백엔드 + 프론트엔드 한번에)
docker compose up -d

# DB 테이블 생성 (최초 1회)
docker compose exec backend alembic upgrade head
```

**방법 B: 직접 실행**

터미널을 2개 열고:

```bash
# 터미널 1 — 백엔드
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
# 터미널 2 — 프론트엔드
cd frontend
npm install
npm run dev
```

### 5단계: 접속

| 주소 | 내용 |
|---|---|
| http://localhost:3000 | 웹 대시보드 |
| http://localhost:8000/docs | 전체 API 목록 (Swagger UI) |

첫 계정 만들기:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "비밀번호",
    "name": "홍길동",
    "role": "admin"
  }'
```

---

## DB 마이그레이션 안내

```bash
# Phase 1 테이블 생성
alembic upgrade 001

# Phase 2 테이블 추가 (에이전트·EVMS·Geofence)
alembic upgrade 002

# 또는 한번에 최신 버전으로
alembic upgrade head
```

---

## 웹 대시보드 화면 구성

서버 실행 후 `http://localhost:3000` 에 접속하면 사용할 수 있는 전체 화면 목록입니다.

### 공통 화면

| 화면 | 주소 | 설명 |
|---|---|---|
| 로그인 | `/login` | 이메일·비밀번호 로그인 |
| 대시보드 | `/dashboard` | 프로젝트별 요약, 오늘 날씨 경보 |
| 프로젝트 목록 | `/projects` | 현장 목록, 신규 프로젝트 등록 |
| 법규 Q&A | `/rag` | 건설 법규·시방서 검색 채팅 |
| 설정 | `/settings` | 발주처 프로파일, 공종 라이브러리 관리 |

### 프로젝트 내 모듈 (10개 탭)

프로젝트 상세 페이지(`/projects/{id}`)에서 아래 탭으로 이동합니다.

| 탭 | 주소 | 설명 |
|---|---|---|
| 📅 공정표 | `/projects/{id}/gantt` | Gantt 차트, CPM 주공정선 시각화 |
| 📋 일보/보고서 | `/projects/{id}/reports` | 작업일보·주간·월간 보고서 목록, PDF 다운로드 |
| 🔬 검측 | `/projects/{id}/inspections` | 검측요청서 목록, AI 생성, PDF 출력 |
| ✅ 품질시험 | `/projects/{id}/quality` | 시험 기록 입력, 합격률 통계 |
| 🌤 날씨 | `/projects/{id}/weather` | 7일 예보, 활성 경보 목록 |
| 🏛 인허가 | `/projects/{id}/permits` | 인허가 체크리스트, AI 자동 도출 |
| 🤖 AI 에이전트 | `/projects/{id}/agents` | GONGSA·PUMJIL·ANJEON·GUMU 채팅, 협업 시나리오 실행, 아침 브리핑 |
| 📊 EVMS | `/projects/{id}/evms` | SPI·CPI 지수, 공정률 추이 차트, 공기 예측, 기성청구 금액 |
| 👁 Vision AI | `/projects/{id}/vision` | 공종 분류 / 안전 점검 / 도면 대조 (탭 전환) |
| 📦 준공도서 | `/projects/{id}/completion` | 준공 준비도 체크리스트, ZIP 패키지 다운로드 |

### 발주처 전용 포털

로그인 없이 접속 가능한 별도 화면입니다. 현장 관리자가 발급한 토큰만 있으면 됩니다.

| 화면 | 주소 | 설명 |
|---|---|---|
| 발주처 포털 | `/portal` | 토큰 입력 → 공사 현황 대시보드 (공정률·SPI·품질합격률·최근 일보) |

---

## 법규 Q&A 기능 (RAG) 설정

법규 Q&A를 사용하려면 먼저 Supabase에서 pgvector를 활성화하세요:

```sql
-- Supabase SQL Editor에서 실행 (최초 1회)
CREATE EXTENSION IF NOT EXISTS vector;
```

그 다음, 법령·시방서 문서를 색인합니다:

```bash
cd backend

# PDF 파일 색인
python scripts/seed_rag.py \
  --file "문서/KCS14 20 10 콘크리트.pdf" \
  --title "KCS 14 20 10 콘크리트 시방서" \
  --type kcs

# 텍스트 파일도 가능
python scripts/seed_rag.py \
  --file "문서/건설기술진흥법.txt" \
  --title "건설기술진흥법" \
  --type law

# 색인된 문서 목록 확인
python scripts/seed_rag.py --list

# 색인 삭제
python scripts/seed_rag.py --delete <source_id>
```

### 공개 자료 출처

| 자료 | 다운로드 |
|---|---|
| KCS 한국건설기준 | [kcsc.re.kr](https://www.kcsc.re.kr) |
| 건설기술진흥법 | [law.go.kr](https://www.law.go.kr) |
| 산업안전보건법 | [law.go.kr](https://www.law.go.kr) |
| 중대재해처벌법 | [law.go.kr](https://www.law.go.kr) |

> ⚠️ 법령 문서는 저작권 확인 후 사용하세요. 국가법령정보센터 자료는 공공누리 조건에 따라 활용 가능합니다.

---

## AI 에이전트 사용법

에이전트는 프로젝트 페이지 또는 API를 통해 대화할 수 있습니다.

**API 예시:**

```bash
# 자동 라우팅 (메시지 내용에 따라 적절한 에이전트 선택)
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/agents/chat \
  -H "Authorization: Bearer {토큰}" \
  -H "Content-Type: application/json" \
  -d '{"content": "오늘 콘크리트 타설 가능한가요?"}'
  # → GONGSA가 날씨·공정 현황 기반으로 답변

# 아침 브리핑 수동 생성
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/agents/briefing \
  -H "Authorization: Bearer {토큰}"

# 에이전트 협업 시나리오 실행
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/agents/scenario/concrete_pour \
  -H "Authorization: Bearer {토큰}"
  # → GONGSA, PUMJIL, ANJEON 순서로 브리핑·체크리스트·TBM 자동 생성
```

---

## 발주처 포털 사용법

발주처에게 공사 현황 링크를 제공할 수 있습니다. 로그인 없이 토큰만으로 접근합니다.

**웹 화면으로 사용:**
1. 포털 토큰 발급 (아래 API 또는 Swagger UI)
2. 발주처에게 URL + 토큰 전달: `http://내도메인/portal`
3. 발주처가 접속 후 토큰 입력 → 공정률·품질·일보 실시간 확인

**API로 사용:**
```bash
# 포털 토큰 발급 (현장 관리자가 실행)
curl -X POST http://localhost:8000/api/v1/portal/tokens \
  -H "Authorization: Bearer {관리자_토큰}" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "프로젝트_ID", "expires_days": 30, "label": "발주처"}'

# 발급된 토큰으로 발주처가 공사 현황 조회
curl http://localhost:8000/api/v1/portal/dashboard \
  -H "Authorization: Bearer {발급된_포털_토큰}"
```

---

## 준공도서 패키지 생성

```bash
# 준공 준비 체크리스트 확인
GET /api/v1/projects/{project_id}/completion/checklist

# 준공도서 ZIP 다운로드 (작업일보·품질시험·검측이력·인허가 현황)
GET /api/v1/projects/{project_id}/completion/download
```

---

## 카카오 챗봇 연동 (선택사항)

1. [Kakao i Open Builder](https://i.kakao.com) 접속
2. 새 챗봇 만들기
3. Skill 서버 URL: `https://내도메인/api/v1/kakao/webhook`
4. 챗봇을 카카오채널에 연결

사용 예시:
- `일보: 콘크리트 5명, 철근 3명, 관로매설 50m 완료` → AI가 작업일보 생성
- `질문: 콘크리트 타설 최저기온은?` → 법규/시방서 검색 후 답변
- `날씨` → 현장 날씨 경보 확인

---

## 프로젝트 구조

```
convai/
├── backend/                      # Python FastAPI 서버
│   ├── app/
│   │   ├── api/                  # REST API 엔드포인트 (16개)
│   │   │   ├── auth.py           # 로그인·회원가입
│   │   │   ├── projects.py       # 프로젝트·WBS 관리
│   │   │   ├── tasks.py          # 태스크·CPM Gantt
│   │   │   ├── daily_reports.py  # 작업일보 + PDF
│   │   │   ├── reports.py        # 주간·월간 보고서 + PDF
│   │   │   ├── inspections.py    # 검측요청서 + PDF
│   │   │   ├── quality.py        # 품질시험 관리
│   │   │   ├── weather.py        # 날씨 연동·경보
│   │   │   ├── rag.py            # 법규 Q&A
│   │   │   ├── kakao.py          # 카카오 챗봇 웹훅
│   │   │   ├── permits.py        # 인허가 + 자동도출
│   │   │   ├── agents.py         # AI 에이전트 4인방 + 협업
│   │   │   ├── evms.py           # EVMS (공정 성과 지수)
│   │   │   ├── vision.py         # Vision AI L1·L2·L3
│   │   │   ├── geofence.py       # 위험구역 Geofence
│   │   │   ├── completion.py     # 준공도서 패키지
│   │   │   ├── documents.py      # 설계도서 파싱·HWP 출력
│   │   │   └── portal.py         # 발주처 전용 포털
│   │   ├── models/               # 데이터베이스 모델 (15개 테이블)
│   │   ├── schemas/              # 입출력 데이터 형식
│   │   ├── services/             # 핵심 비즈니스 로직
│   │   │   ├── agents/           # AI 에이전트 (GONGSA·PUMJIL·ANJEON·GUMU)
│   │   │   ├── ai_engine.py      # Claude API 래퍼
│   │   │   ├── gantt.py          # CPM 주공정선 계산
│   │   │   ├── weather_service.py # 기상청 API
│   │   │   ├── rag_service.py    # 법규 검색 (pgvector)
│   │   │   ├── pdf_service.py    # PDF 생성 (WeasyPrint)
│   │   │   ├── vision_service.py # Vision AI (Claude Vision)
│   │   │   ├── evms_service.py   # EVMS 계산
│   │   │   ├── completion_service.py # 준공도서 패키지
│   │   │   ├── document_parser.py # 설계도서 파싱
│   │   │   └── scheduler.py      # 자동 배치 (날씨·EVMS·브리핑)
│   │   ├── templates/            # PDF·준공도서 HTML 템플릿
│   │   └── core/                 # 보안·DB·파일저장
│   ├── alembic/                  # DB 마이그레이션 (001·002)
│   ├── scripts/
│   │   └── seed_rag.py           # 법규 문서 색인 도구
│   └── tests/                    # 단위 테스트
│
├── frontend/                     # Next.js 웹 대시보드
│   └── src/
│       ├── app/                  # 페이지 (16개)
│       │   ├── login/            # 로그인
│       │   ├── dashboard/        # 메인 대시보드
│       │   ├── projects/         # 프로젝트 목록
│       │   ├── projects/[id]/    # 프로젝트 상세
│       │   │   ├── gantt/        # 공정표
│       │   │   ├── reports/      # 일보·보고서
│       │   │   ├── inspections/  # 검측
│       │   │   ├── quality/      # 품질시험
│       │   │   ├── weather/      # 날씨 경보
│       │   │   ├── permits/      # 인허가
│       │   │   ├── agents/       # AI 에이전트 채팅
│       │   │   ├── evms/         # EVMS 대시보드
│       │   │   ├── vision/       # Vision AI
│       │   │   └── completion/   # 준공도서 패키지
│       │   ├── rag/              # 법규 Q&A
│       │   ├── settings/         # 설정
│       │   └── portal/           # 발주처 포털
│       ├── components/           # UI 컴포넌트
│       ├── hooks/                # React 훅
│       └── lib/                  # API 클라이언트·타입·유틸
│
├── docs/setup.md                 # 상세 설치 가이드
├── docker-compose.yml            # Docker 개발 환경
└── README.md
```

---

## 자동화 스케줄

서버가 실행되면 아래 작업이 자동으로 실행됩니다:

| 시간 | 작업 |
|---|---|
| 매 3시간 | 활성 프로젝트 날씨 데이터 수집 + 경보 평가 |
| 매일 00:05 | EVMS 스냅샷 자동 저장 (공정률·지수) |
| 매일 07:00 | GONGSA 아침 공정 브리핑 자동 생성 |

---

## 기여하기

버그 신고, 기능 제안, 코드 기여 모두 환영합니다!

1. 이 저장소를 Fork
2. 새 브랜치 만들기: `git checkout -b feature/기능명`
3. 변경사항 커밋: `git commit -m "feat: 새 기능 추가"`
4. Push: `git push origin feature/기능명`
5. Pull Request 열기

**이슈 등록**: [GitHub Issues](https://github.com/sinmb79/convai/issues)

---

## 기술 스택

| 분야 | 기술 |
|---|---|
| AI | Claude API (Sonnet), Claude Vision, Voyage AI 임베딩 |
| 백엔드 | Python 3.11, FastAPI, SQLAlchemy async, Alembic |
| 프론트엔드 | Next.js 15, React 19, TanStack Query, Tailwind CSS, Zustand |
| 데이터베이스 | PostgreSQL (Supabase) + pgvector (RAG 벡터 검색) |
| PDF 출력 | WeasyPrint + Jinja2 |
| HWP 출력 | Pandoc (선택, 별도 설치 필요) |
| 챗봇 | 카카오 Skill API |
| 날씨 | 기상청 단기예보 Open API |
| 스케줄러 | APScheduler |
| 배포 | Docker Compose, Railway 지원 |

---

## 오픈소스 범위

이 저장소의 모든 코드는 **MIT 라이선스**로 공개됩니다.
자유롭게 사용, 수정, 배포, 상업적 활용이 가능합니다.

---

## 법적 고지

- AI가 생성한 작업일보·보고서는 **반드시 담당자가 검토·확인** 후 사용하세요
- 법규·시방서 Q&A는 **참고용**이며 법률 자문이 아닙니다
- Vision AI 사진 분석 결과는 **1차 보조 판독**이며, 최종 판정은 현장 책임자가 합니다
- 안전 관련 기능은 전문 안전관리자를 **대체하지 않습니다**
- 모든 AI 생성 문서의 최종 책임은 현장 책임자에게 있습니다

---

## 라이선스

[MIT License](LICENSE) — Copyright (c) 2026 22B Labs / The 4th Path

---

## 만든 곳

**22B Labs / The 4th Path**
소형 건설업체의 디지털 전환을 돕습니다.

> "대형사가 12~22명으로 하는 일을 소형업체 1~2명이 AI와 함께 해낼 수 있도록"
