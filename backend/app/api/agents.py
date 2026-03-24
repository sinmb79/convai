"""
AI 에이전트 API
- 대화 생성/조회/삭제
- 메시지 전송 (에이전트 응답 반환)
- 에이전트 자동 라우팅
- 프로액티브 브리핑 (아침 공정 브리핑 등)
"""
import uuid
from datetime import date
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DB
from app.models.agent import AgentConversation, AgentMessage, AgentType, ConversationStatus
from app.models.project import Project
from app.services.agents.router import get_agent, route_by_keyword

router = APIRouter(prefix="/projects/{project_id}/agents", tags=["AI 에이전트"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class ConversationCreate(BaseModel):
    agent_type: AgentType
    title: str | None = None


class MessageSend(BaseModel):
    content: str
    agent_type: AgentType | None = None  # None이면 자동 라우팅


class ConversationResponse(BaseModel):
    id: uuid.UUID
    agent_type: AgentType
    title: str | None
    status: ConversationStatus
    message_count: int = 0
    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    is_proactive: bool
    metadata: dict | None
    model_config = {"from_attributes": True}


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _get_project_or_404(project_id: uuid.UUID, db: DB) -> Project:
    r = await db.execute(select(Project).where(Project.id == project_id))
    p = r.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return p


async def _get_conversation_or_404(
    conv_id: uuid.UUID, project_id: uuid.UUID, db: DB
) -> AgentConversation:
    r = await db.execute(
        select(AgentConversation)
        .where(AgentConversation.id == conv_id, AgentConversation.project_id == project_id)
        .options(selectinload(AgentConversation.messages))
    )
    conv = r.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다")
    return conv


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("", response_model=list[ConversationResponse])
async def list_conversations(project_id: uuid.UUID, db: DB, current_user: CurrentUser):
    r = await db.execute(
        select(AgentConversation)
        .where(AgentConversation.project_id == project_id)
        .options(selectinload(AgentConversation.messages))
        .order_by(AgentConversation.updated_at.desc())
    )
    convs = r.scalars().all()
    result = []
    for c in convs:
        d = ConversationResponse(
            id=c.id,
            agent_type=c.agent_type,
            title=c.title,
            status=c.status,
            message_count=len(c.messages),
        )
        result.append(d)
    return result


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    project_id: uuid.UUID, data: ConversationCreate, db: DB, current_user: CurrentUser
):
    await _get_project_or_404(project_id, db)
    conv = AgentConversation(
        project_id=project_id,
        user_id=current_user.id,
        agent_type=data.agent_type,
        title=data.title or f"{data.agent_type.value.upper()} 대화",
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return ConversationResponse(
        id=conv.id, agent_type=conv.agent_type, title=conv.title,
        status=conv.status, message_count=0,
    )


@router.get("/{conv_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    project_id: uuid.UUID, conv_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    conv = await _get_conversation_or_404(conv_id, project_id, db)
    return conv.messages


@router.post("/{conv_id}/messages", response_model=MessageResponse)
async def send_message(
    project_id: uuid.UUID,
    conv_id: uuid.UUID,
    data: MessageSend,
    db: DB,
    current_user: CurrentUser,
):
    """메시지 전송 → 에이전트 응답 반환"""
    conv = await _get_conversation_or_404(conv_id, project_id, db)

    # 사용자 메시지 저장
    user_msg = AgentMessage(
        conversation_id=conv.id,
        role="user",
        content=data.content,
    )
    db.add(user_msg)
    await db.flush()

    # 대화 히스토리 구성 (최근 20개)
    history = [
        {"role": m.role, "content": m.content}
        for m in conv.messages[-20:]
        if m.role in ("user", "assistant")
    ]
    history.append({"role": "user", "content": data.content})

    # 에이전트 선택 (대화에 지정된 에이전트 사용)
    agent = get_agent(conv.agent_type)

    # 컨텍스트 조회 및 응답 생성
    context = await agent.build_context(db, str(project_id))
    reply = await agent.chat(messages=history, context=context)

    # 에이전트 응답 저장
    agent_msg = AgentMessage(
        conversation_id=conv.id,
        role="assistant",
        content=reply,
    )
    db.add(agent_msg)
    await db.commit()
    await db.refresh(agent_msg)
    return agent_msg


@router.post("/chat", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def quick_chat(
    project_id: uuid.UUID,
    data: MessageSend,
    db: DB,
    current_user: CurrentUser,
):
    """
    새 대화 없이 바로 메시지 전송 (에이전트 자동 라우팅).
    자동으로 대화 세션을 생성하고 첫 응답을 반환합니다.
    """
    await _get_project_or_404(project_id, db)

    # 에이전트 자동 라우팅
    agent_type = data.agent_type or route_by_keyword(data.content)
    agent = get_agent(agent_type)

    # 새 대화 생성
    conv = AgentConversation(
        project_id=project_id,
        user_id=current_user.id,
        agent_type=agent_type,
        title=data.content[:50],
    )
    db.add(conv)
    await db.flush()

    # 사용자 메시지 저장
    user_msg = AgentMessage(
        conversation_id=conv.id, role="user", content=data.content
    )
    db.add(user_msg)
    await db.flush()

    # 응답 생성
    context = await agent.build_context(db, str(project_id))
    reply = await agent.chat(
        messages=[{"role": "user", "content": data.content}],
        context=context,
    )

    agent_msg = AgentMessage(
        conversation_id=conv.id, role="assistant", content=reply
    )
    db.add(agent_msg)
    await db.commit()
    await db.refresh(agent_msg)
    return agent_msg


@router.post("/briefing", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def morning_briefing(
    project_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """
    GONGSA 아침 공정 브리핑 생성 (오전 7시 자동 호출 또는 수동 호출).
    오늘 날씨 + 예정 공종 + 전일 실적 기반으로 브리핑을 생성합니다.
    """
    await _get_project_or_404(project_id, db)
    from app.services.agents.gongsa import gongsa_agent

    context = await gongsa_agent.build_context(db, str(project_id))

    prompt = (
        f"오늘({context.get('today', date.today())}) 아침 공정 브리핑을 작성해주세요. "
        "날씨, 오늘 예정 공종, 주의사항을 포함해주세요."
    )

    conv = AgentConversation(
        project_id=project_id,
        user_id=current_user.id,
        agent_type=AgentType.GONGSA,
        title=f"{context.get('today', '')} 아침 브리핑",
    )
    db.add(conv)
    await db.flush()

    reply = await gongsa_agent.chat(
        messages=[{"role": "user", "content": prompt}],
        context=context,
    )

    msg = AgentMessage(
        conversation_id=conv.id, role="assistant", content=reply, is_proactive=True
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


@router.delete("/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    project_id: uuid.UUID, conv_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    conv = await _get_conversation_or_404(conv_id, project_id, db)
    await db.delete(conv)
    await db.commit()
