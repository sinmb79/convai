"""
에이전트 협업 고도화 — Phase 3
복수 에이전트가 순차적으로 하나의 시나리오를 처리합니다.

예시: 콘크리트 타설 당일 시나리오
  07:00 GONGSA → 공정 브리핑 + 날씨 체크
  07:05 PUMJIL → 타설 전 품질 체크리스트
  07:10 ANJEON → TBM 자료 + 안전 체크
"""
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.agent import AgentConversation, AgentMessage, AgentType
from .gongsa import gongsa_agent
from .pumjil import pumjil_agent
from .anjeon import anjeon_agent
from .gumu import gumu_agent
from .base import BaseAgent


SCENARIO_AGENTS = {
    "concrete_pour": [
        (AgentType.GONGSA, "콘크리트 타설 예정입니다. 날씨와 공정 현황을 브리핑해주세요."),
        (AgentType.PUMJIL, "오늘 콘크리트 타설 전 품질 체크리스트를 발송해주세요."),
        (AgentType.ANJEON, "콘크리트 타설 작업 TBM 자료를 작성해주세요."),
    ],
    "excavation": [
        (AgentType.GONGSA, "굴착 작업 예정입니다. 공정 현황을 브리핑해주세요."),
        (AgentType.ANJEON, "굴착 작업 안전 사전 경보와 TBM 자료를 작성해주세요."),
        (AgentType.PUMJIL, "굴착 작업 품질 관리 체크리스트를 발송해주세요."),
    ],
    "weekly_report": [
        (AgentType.GONGSA, "이번 주 공정 현황을 요약해주세요."),
        (AgentType.PUMJIL, "이번 주 품질시험 및 검측 현황을 요약해주세요."),
        (AgentType.GUMU,   "이번 주 행정 처리 현황과 다음 주 예정 사항을 정리해주세요."),
    ],
}


async def run_scenario(
    db: AsyncSession,
    project_id,
    user_id,
    scenario: str,
) -> list[dict]:
    """
    협업 시나리오 실행.
    반환: [{"agent": "gongsa", "content": "...", "message_id": "..."}, ...]
    """
    import uuid
    pid = uuid.UUID(str(project_id))

    steps = SCENARIO_AGENTS.get(scenario)
    if not steps:
        raise ValueError(f"알 수 없는 시나리오: {scenario}. 가능한 값: {list(SCENARIO_AGENTS.keys())}")

    results = []
    agent_map: dict[AgentType, BaseAgent] = {
        AgentType.GONGSA: gongsa_agent,
        AgentType.PUMJIL: pumjil_agent,
        AgentType.ANJEON: anjeon_agent,
        AgentType.GUMU:   gumu_agent,
    }

    # 이전 에이전트 응답을 컨텍스트에 누적
    prev_responses: list[str] = []

    for agent_type, prompt_base in steps:
        agent = agent_map[agent_type]
        context = await agent.build_context(db, str(pid))

        # 이전 에이전트 응답을 프롬프트에 추가
        prompt = prompt_base
        if prev_responses:
            prompt += "\n\n이전 에이전트 응답 요약:\n" + "\n---\n".join(prev_responses[-2:])

        # 대화 세션 생성
        conv = AgentConversation(
            project_id=pid,
            user_id=uuid.UUID(str(user_id)),
            agent_type=agent_type,
            title=f"{scenario} 협업 시나리오 ({date.today()})",
        )
        db.add(conv)
        await db.flush()

        reply = await agent.chat(
            messages=[{"role": "user", "content": prompt}],
            context=context,
        )

        msg = AgentMessage(
            conversation_id=conv.id,
            role="assistant",
            content=reply,
            is_proactive=True,
            metadata={"scenario": scenario, "step": agent_type.value},
        )
        db.add(msg)
        await db.flush()

        prev_responses.append(f"[{agent_type.value.upper()}] {reply[:300]}")
        results.append({
            "agent": agent_type.value,
            "agent_name": agent.name_ko,
            "content": reply,
            "conversation_id": str(conv.id),
            "message_id": str(msg.id),
        })

    await db.commit()
    return results
