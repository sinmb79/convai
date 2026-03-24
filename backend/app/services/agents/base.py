"""
에이전트 베이스 클래스
각 에이전트는 독립된 페르소나 + Claude 인스턴스로 구동됩니다.
- 엔진 DB를 공유하여 프로젝트 데이터 접근
- 에이전트는 제안하고, 사람이 결정합니다
- 모든 대화는 DB에 기록됩니다
"""
from abc import ABC, abstractmethod
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_engine import complete


class BaseAgent(ABC):
    """모든 에이전트의 공통 베이스"""

    agent_type: str
    name_ko: str

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """에이전트 고유 시스템 프롬프트"""
        ...

    async def chat(
        self,
        messages: list[dict],
        context: dict | None = None,
        temperature: float = 0.5,
    ) -> str:
        """
        대화 수행
        messages: [{"role": "user"|"assistant", "content": "..."}]
        context:  프로젝트/날씨/태스크 등 컨텍스트 (시스템 프롬프트에 주입)
        """
        system = self.system_prompt
        if context:
            system += "\n\n## 현재 컨텍스트\n" + self._format_context(context)

        return await complete(
            messages=messages,
            system=system,
            temperature=temperature,
            max_tokens=2048,
        )

    def _format_context(self, context: dict) -> str:
        lines = []
        if context.get("project_name"):
            lines.append(f"- 프로젝트: {context['project_name']}")
        if context.get("today"):
            lines.append(f"- 오늘 날짜: {context['today']}")
        if context.get("weather"):
            lines.append(f"- 오늘 날씨: {context['weather']}")
        if context.get("active_tasks"):
            lines.append(f"- 진행 중 공종: {', '.join(context['active_tasks'])}")
        if context.get("pending_inspections"):
            lines.append(f"- 미완료 검측: {context['pending_inspections']}건")
        if context.get("overdue_tests"):
            lines.append(f"- 기한 초과 품질시험: {context['overdue_tests']}건")
        if context.get("overdue_permits"):
            lines.append(f"- 지연 인허가: {context['overdue_permits']}건")
        if context.get("schedule_delay_days"):
            lines.append(f"- 공정 지연: {context['schedule_delay_days']}일")
        return "\n".join(lines)

    async def build_context(self, db: AsyncSession, project_id: str) -> dict:
        """프로젝트 컨텍스트를 DB에서 조회하여 반환"""
        from datetime import date
        from sqlalchemy import select, func
        from app.models.project import Project
        from app.models.task import Task
        from app.models.weather import WeatherData
        from app.models.inspection import InspectionRequest, InspectionStatus
        from app.models.permit import PermitItem

        import uuid
        pid = uuid.UUID(str(project_id))

        # 프로젝트 정보
        proj_r = await db.execute(select(Project).where(Project.id == pid))
        project = proj_r.scalar_one_or_none()
        if not project:
            return {}

        # 오늘 날씨
        today = date.today()
        weather_r = await db.execute(
            select(WeatherData).where(WeatherData.project_id == pid, WeatherData.forecast_date == today)
        )
        weather = weather_r.scalar_one_or_none()
        weather_summary = None
        if weather:
            parts = []
            if weather.sky_condition:
                parts.append(weather.sky_condition)
            if weather.temperature_max is not None:
                parts.append(f"최고 {weather.temperature_max:.0f}°C")
            if weather.precipitation_mm and weather.precipitation_mm > 0:
                parts.append(f"강수 {weather.precipitation_mm:.1f}mm")
            weather_summary = " / ".join(parts) if parts else None

        # 진행 중 태스크
        tasks_r = await db.execute(
            select(Task).where(Task.project_id == pid, Task.status.in_(["in_progress", "not_started"]))
        )
        tasks = tasks_r.scalars().all()
        active_tasks = list({t.name for t in tasks if t.status == "in_progress"})[:5]

        # 미완료 검측
        insp_r = await db.execute(
            select(func.count()).where(
                InspectionRequest.project_id == pid,
                InspectionRequest.status == InspectionStatus.DRAFT,
            )
        )
        pending_inspections = insp_r.scalar() or 0

        # 지연 인허가
        permit_r = await db.execute(
            select(func.count()).where(
                PermitItem.project_id == pid,
                PermitItem.status.in_(["pending", "in_progress"]),
                PermitItem.due_date < today,
            )
        )
        overdue_permits = permit_r.scalar() or 0

        return {
            "project_name": project.name,
            "today": str(today),
            "weather": weather_summary,
            "active_tasks": active_tasks,
            "pending_inspections": pending_inspections,
            "overdue_permits": overdue_permits,
        }
