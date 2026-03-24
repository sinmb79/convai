"""
에이전트 라우터
사용자 메시지의 의도를 파악하여 적절한 에이전트로 분배합니다.
"""
from app.models.agent import AgentType
from .gongsa import gongsa_agent
from .pumjil import pumjil_agent
from .anjeon import anjeon_agent
from .gumu import gumu_agent
from .base import BaseAgent

# 에이전트 레지스트리
AGENTS: dict[AgentType, BaseAgent] = {
    AgentType.GONGSA: gongsa_agent,
    AgentType.PUMJIL: pumjil_agent,
    AgentType.ANJEON: anjeon_agent,
    AgentType.GUMU:   gumu_agent,
}

# 키워드 기반 자동 라우팅
_ROUTING_RULES: list[tuple[list[str], AgentType]] = [
    # 공사/공정
    (["공정", "일정", "지연", "타설", "굴착", "공기", "브리핑", "작업", "일보", "진도"], AgentType.GONGSA),
    # 품질
    (["품질", "시험", "검사", "슬럼프", "압축강도", "합격", "불합격", "KCS", "시방서", "체크리스트"], AgentType.PUMJIL),
    # 안전
    (["안전", "사고", "위험", "TBM", "교육", "중대재해", "보호구", "추락", "굴착 안전", "Geofence", "지오펜스"], AgentType.ANJEON),
    # 공무
    (["인허가", "허가", "신고", "기성", "보고서", "발주처", "행정", "서류", "청구"], AgentType.GUMU),
]


def route_by_keyword(message: str) -> AgentType:
    """키워드 매칭으로 적절한 에이전트 타입을 반환. 매칭 없으면 GONGSA."""
    msg_lower = message.lower()
    scores: dict[AgentType, int] = {t: 0 for t in AgentType}
    for keywords, agent_type in _ROUTING_RULES:
        for kw in keywords:
            if kw in msg_lower:
                scores[agent_type] += 1
    best = max(scores, key=lambda t: scores[t])
    return best if scores[best] > 0 else AgentType.GONGSA


def get_agent(agent_type: AgentType) -> BaseAgent:
    return AGENTS[agent_type]
