"""
Vision AI Level 1 — 현장 사진 분류 서비스
Claude Vision API를 사용하여:
- 공종 자동 분류
- 날짜/위치 태깅 (EXIF 또는 수동)
- 이상 후보 감지 (안전장비 미착용 등)
- 작업일보 자동 첨부용 캡션 생성
"""
import base64
from anthropic import AsyncAnthropic
from app.config import settings

_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

WORK_TYPE_LIST = [
    "콘크리트 타설", "철근 배근", "거푸집 설치/해체", "터파기/굴착",
    "흙막이 공사", "다짐", "관 매설", "아스팔트 포장",
    "고소 작업", "크레인 작업", "안전 시설물", "현장 전경", "기타",
]

_SYSTEM = """당신은 건설 현장 사진을 분석하는 AI입니다.
사진을 보고 다음을 정확히 분석하세요:
1. 공종 분류 (단 하나 선택)
2. 진행 상태 (시작 전 / 진행 중 / 완료)
3. 안전장비 착용 여부 (안전모, 안전조끼 식별 가능한 경우)
4. 특이사항 (이상 징후, 주의 필요 사항)
5. 작업일보용 간략 설명 (1-2문장, 한국어)

JSON 형식으로만 응답하세요."""

_USER_TEMPLATE = """이 건설 현장 사진을 분석해주세요.

공종 목록: {work_types}

다음 JSON 형식으로만 응답하세요:
{{
  "work_type": "콘크리트 타설",
  "status": "진행 중",
  "safety_ok": true,
  "safety_issues": [],
  "anomalies": [],
  "caption": "3공구 기초 콘크리트 타설 작업 진행 중",
  "confidence": 0.85
}}"""


async def classify_photo(
    image_data: bytes,
    media_type: str = "image/jpeg",
    location_hint: str | None = None,
) -> dict:
    """
    현장 사진 분류
    image_data: 이미지 바이너리
    media_type: image/jpeg, image/png, image/webp
    location_hint: 위치 힌트 (예: "3공구", "A구역")

    반환:
    {
        "work_type": str,
        "status": str,
        "safety_ok": bool,
        "safety_issues": list[str],
        "anomalies": list[str],
        "caption": str,
        "confidence": float,
        "location_hint": str | None,
    }
    """
    image_b64 = base64.standard_b64encode(image_data).decode()

    user_content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": image_b64,
            },
        },
        {
            "type": "text",
            "text": _USER_TEMPLATE.format(work_types=", ".join(WORK_TYPE_LIST))
            + (f"\n\n위치 정보: {location_hint}" if location_hint else ""),
        },
    ]

    response = await _client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=512,
        system=_SYSTEM,
        messages=[{"role": "user", "content": user_content}],
    )

    raw = response.content[0].text.strip()

    # JSON 파싱
    import json, re
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        result = json.loads(json_match.group())
    else:
        result = {
            "work_type": "기타",
            "status": "확인 필요",
            "safety_ok": None,
            "safety_issues": [],
            "anomalies": ["AI 분석 실패 — 수동 확인 필요"],
            "caption": raw[:100],
            "confidence": 0.0,
        }

    result["location_hint"] = location_hint
    return result


async def analyze_safety(
    image_data: bytes,
    media_type: str = "image/jpeg",
) -> dict:
    """
    Vision AI Level 2 — 안전장비 착용 감지 (안전모/안전조끼)
    PPE(Personal Protective Equipment) 착용 여부 집중 분석
    """
    image_b64 = base64.standard_b64encode(image_data).decode()

    safety_prompt = """이 건설 현장 사진에서 안전장비 착용 여부를 분석하세요.

다음 JSON 형식으로만 응답하세요:
{
  "worker_count": 3,
  "helmet_worn": [true, true, false],
  "vest_worn": [true, false, true],
  "violations": ["3번 작업자: 안전모 미착용"],
  "risk_level": "중",
  "recommendation": "안전모 미착용 작업자 즉시 착용 조치 필요"
}

risk_level: 저(모두 착용) / 중(일부 미착용) / 고(다수 미착용 또는 고소 작업)"""

    response = await _client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": image_b64},
                },
                {"type": "text", "text": safety_prompt},
            ],
        }],
    )

    raw = response.content[0].text.strip()
    import json, re
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return {"error": "분석 실패", "raw": raw[:200]}
