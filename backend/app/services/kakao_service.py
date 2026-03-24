"""
Kakao Chatbot Skill API service.
Parses incoming messages and routes to appropriate handlers.
"""
import re
from datetime import date


# Kakao Skill response builders
def simple_text(text: str) -> dict:
    return {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": text}}]
        }
    }


def basic_card(title: str, description: str, buttons: list[dict] | None = None) -> dict:
    card = {"title": title, "description": description}
    if buttons:
        card["buttons"] = buttons
    return {
        "version": "2.0",
        "template": {
            "outputs": [{"basicCard": card}]
        }
    }


def list_card(header_title: str, items: list[dict], buttons: list[dict] | None = None) -> dict:
    card = {
        "header": {"title": header_title},
        "items": items,
    }
    if buttons:
        card["buttons"] = buttons
    return {
        "version": "2.0",
        "template": {
            "outputs": [{"listCard": card}]
        }
    }


# Message routing
class KakaoIntent:
    DAILY_REPORT = "daily_report"
    RAG_QUESTION = "rag_question"
    WEATHER = "weather"
    HELP = "help"
    UNKNOWN = "unknown"


def detect_intent(utterance: str) -> str:
    """Detect user intent from utterance."""
    u = utterance.strip()

    # Daily report keywords
    if any(k in u for k in ["일보", "작업일보", "오늘 공사", "금일 공사"]):
        return KakaoIntent.DAILY_REPORT

    # RAG / question keywords
    if any(k in u for k in ["질문", "법규", "시방서", "기준", "KCS", "법령", "산안법", "중대재해", "?", "？"]):
        return KakaoIntent.RAG_QUESTION

    # Weather keywords
    if any(k in u for k in ["날씨", "기상", "비", "눈", "바람"]):
        return KakaoIntent.WEATHER

    # Help
    if any(k in u for k in ["도움말", "메뉴", "help", "사용법"]):
        return KakaoIntent.HELP

    return KakaoIntent.UNKNOWN


def parse_daily_report_input(utterance: str) -> dict:
    """
    Parse daily report input from free-form Kakao message.
    Example: "오늘 일보: 콘크리트 5명, 철근 3명, 관로매설 오후 완료"
    """
    workers = {}
    work_items = []
    issues = None

    # Extract worker counts: "직종 N명" patterns
    worker_pattern = re.findall(r'([가-힣a-zA-Z]+)\s+(\d+)명', utterance)
    for role, count in worker_pattern:
        if role not in ["총", "합계"]:
            workers[role] = int(count)

    # Extract work items after "일보:" or newlines
    lines = utterance.replace("일보:", "").replace("작업일보:", "").split("\n")
    for line in lines:
        line = line.strip().lstrip("-").strip()
        if line and len(line) > 2 and not re.search(r'\d+명', line):
            work_items.append(line)

    # Check for issues
    if "특이" in utterance or "문제" in utterance or "이슈" in utterance:
        issue_match = re.search(r'(특이|문제|이슈)[사항:：\s]*(.+?)(?:\n|$)', utterance)
        if issue_match:
            issues = issue_match.group(2).strip()

    return {
        "workers_count": workers,
        "work_items": work_items if work_items else ["기타 작업"],
        "issues": issues,
        "report_date": str(date.today()),
    }


def make_help_response() -> dict:
    return list_card(
        header_title="CONAI 현장 도우미",
        items=[
            {"title": "작업일보 작성", "description": "일보: 작업내용 입력"},
            {"title": "법규 질문", "description": "질문: 궁금한 내용 입력"},
            {"title": "날씨 확인", "description": "날씨 입력"},
        ],
        buttons=[{"action": "message", "label": "일보 작성", "messageText": "일보:"}],
    )
