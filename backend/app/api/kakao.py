"""
Kakao Chatbot Skill API webhook endpoints.
"""
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select
from app.deps import DB
from app.models.user import User
from app.models.project import Project
from app.models.daily_report import DailyReport, InputSource
from app.services.kakao_service import (
    detect_intent, parse_daily_report_input, make_help_response,
    simple_text, basic_card, KakaoIntent,
)
from app.services.daily_report_gen import generate_work_content
from app.services.rag_service import ask as rag_ask

router = APIRouter(prefix="/kakao", tags=["카카오 챗봇"])


@router.post("/webhook")
async def kakao_webhook(request: Request, db: DB):
    """Main Kakao Skill webhook. Routes to appropriate handler."""
    body = await request.json()

    # Extract user info and utterance
    user_request = body.get("userRequest", {})
    utterance = user_request.get("utterance", "")
    user_key = user_request.get("user", {}).get("id", "")

    # Find linked user
    user = None
    if user_key:
        result = await db.execute(select(User).where(User.kakao_user_key == user_key, User.is_active == True))
        user = result.scalar_one_or_none()

    if not user:
        return simple_text(
            "안녕하세요! CONAI 현장 관리 시스템입니다.\n"
            "서비스를 이용하시려면 웹에서 계정을 연결해주세요.\n"
            "📱 conai.app에서 카카오 연동 설정"
        )

    intent = detect_intent(utterance)

    if intent == KakaoIntent.DAILY_REPORT:
        return await _handle_daily_report(utterance, user, db)
    elif intent == KakaoIntent.RAG_QUESTION:
        return await _handle_rag_question(utterance, user, db)
    elif intent == KakaoIntent.WEATHER:
        return await _handle_weather(user, db)
    elif intent == KakaoIntent.HELP:
        return make_help_response()
    else:
        return make_help_response()


async def _handle_daily_report(utterance: str, user: User, db: DB) -> dict:
    """Parse utterance and generate/save daily report."""
    # Get user's active project
    project_result = await db.execute(
        select(Project).where(Project.owner_id == user.id, Project.status == "active").limit(1)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        return simple_text("현재 진행 중인 현장이 없습니다. CONAI 웹에서 현장을 등록해주세요.")

    parsed = parse_daily_report_input(utterance)

    if not parsed.get("work_items"):
        return simple_text(
            "작업 내용을 입력해주세요.\n\n"
            "예시:\n"
            "일보: 콘크리트 5명, 철근 3명\n"
            "- 관로매설 50m 완료\n"
            "- 되메우기 작업"
        )

    try:
        work_content = await generate_work_content(
            project_name=project.name,
            report_date=parsed["report_date"],
            weather_summary="맑음",
            temperature_high=None,
            temperature_low=None,
            workers_count=parsed["workers_count"],
            equipment_list=[],
            work_items=parsed["work_items"],
            issues=parsed.get("issues"),
        )
    except Exception as e:
        work_content = "\n".join(parsed["work_items"])

    from datetime import date
    report = DailyReport(
        project_id=project.id,
        report_date=date.fromisoformat(parsed["report_date"]),
        workers_count=parsed.get("workers_count"),
        work_content=work_content,
        issues=parsed.get("issues"),
        input_source=InputSource.KAKAO,
        raw_kakao_input=utterance,
        ai_generated=True,
    )
    db.add(report)
    await db.commit()

    workers_text = ", ".join([f"{k} {v}명" for k, v in (parsed.get("workers_count") or {}).items()])
    return basic_card(
        title=f"📋 {parsed['report_date']} 작업일보 생성완료",
        description=f"현장: {project.name}\n투입인원: {workers_text or '미기입'}\n\n{work_content[:200]}...",
        buttons=[{"action": "webLink", "label": "일보 확인/수정", "webLinkUrl": f"https://conai.app/projects/{project.id}/reports"}],
    )


async def _handle_rag_question(utterance: str, user: User, db: DB) -> dict:
    """Handle RAG Q&A from Kakao."""
    question = utterance.replace("질문:", "").replace("질문 ", "").strip()
    if not question:
        return simple_text("질문 내용을 입력해주세요.\n예: 질문: 굴착 5m 흙막이 기준은?")

    try:
        result = await rag_ask(db, question, top_k=3)
        answer = result.get("answer", "답변을 생성할 수 없습니다")
        # Truncate for Kakao (2000 char limit)
        if len(answer) > 900:
            answer = answer[:900] + "...\n\n[전체 답변은 CONAI 웹에서 확인하세요]"
        return simple_text(f"📚 {question}\n\n{answer}\n\n⚠️ 이 답변은 참고용이며 법률 자문이 아닙니다.")
    except Exception as e:
        return simple_text("현재 Q&A 서비스를 이용할 수 없습니다. 잠시 후 다시 시도해주세요.")


async def _handle_weather(user: User, db: DB) -> dict:
    """Return weather summary for user's active project."""
    project_result = await db.execute(
        select(Project).where(Project.owner_id == user.id, Project.status == "active").limit(1)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        return simple_text("진행 중인 현장이 없습니다.")

    from app.models.weather import WeatherAlert
    from datetime import date
    alerts_result = await db.execute(
        select(WeatherAlert)
        .where(WeatherAlert.project_id == project.id, WeatherAlert.alert_date >= date.today(), WeatherAlert.is_acknowledged == False)
        .limit(5)
    )
    alerts = alerts_result.scalars().all()

    if not alerts:
        return simple_text(f"🌤 {project.name}\n\n현재 날씨 경보가 없습니다.")

    alert_text = "\n".join([f"⚠️ {a.alert_date}: {a.message}" for a in alerts])
    return simple_text(f"🌦 {project.name} 날씨 경보\n\n{alert_text}")
