"""
APScheduler 날씨 자동 수집 배치
- 3시간마다 활성 프로젝트의 날씨 데이터를 수집
- 수집 후 날씨 경보 평가
"""
import logging
from datetime import date, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.project import Project
from app.models.weather import WeatherData, WeatherAlert
from app.services.weather_service import fetch_short_term_forecast, evaluate_alerts

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _collect_weather_for_all_projects():
    """활성 프로젝트 전체의 날씨를 수집하고 경보를 평가합니다."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Project).where(Project.status == "active")
        )
        projects = result.scalars().all()

        if not projects:
            return

        logger.info(f"날씨 수집 시작: {len(projects)}개 프로젝트")

        for project in projects:
            # 프로젝트에 KMA 격자 좌표가 없으면 스킵
            if not project.kma_nx or not project.kma_ny:
                continue

            try:
                forecasts = await fetch_short_term_forecast(project.kma_nx, project.kma_ny)

                today = date.today().isoformat()
                today_forecasts = [f for f in forecasts if f.get("date") == today]

                if today_forecasts:
                    # 오늘 날씨 데이터 upsert (중복 저장 방지)
                    existing = await db.execute(
                        select(WeatherData).where(
                            WeatherData.project_id == project.id,
                            WeatherData.forecast_date == date.today(),
                        )
                    )
                    weather_row = existing.scalar_one_or_none()

                    if not weather_row:
                        # 최고/최저 기온 계산
                        temps = [f.get("temperature") for f in today_forecasts if f.get("temperature") is not None]
                        precips = [f.get("precipitation_mm", 0) or 0 for f in today_forecasts]
                        wind_speeds = [f.get("wind_speed", 0) or 0 for f in today_forecasts]

                        weather_row = WeatherData(
                            project_id=project.id,
                            forecast_date=date.today(),
                            temperature_max=max(temps) if temps else None,
                            temperature_min=min(temps) if temps else None,
                            precipitation_mm=sum(precips),
                            wind_speed_max=max(wind_speeds) if wind_speeds else None,
                            sky_condition=today_forecasts[0].get("sky_condition"),
                            raw_forecast=today_forecasts,
                        )
                        db.add(weather_row)
                        await db.flush()

                    # 날씨 경보 평가 (활성 태스크 기반)
                    from app.models.task import Task
                    tasks_result = await db.execute(
                        select(Task).where(
                            Task.project_id == project.id,
                            Task.status.in_(["not_started", "in_progress"]),
                        )
                    )
                    tasks = tasks_result.scalars().all()

                    # 오늘 이미 생성된 경보 확인
                    existing_alerts = await db.execute(
                        select(WeatherAlert).where(
                            WeatherAlert.project_id == project.id,
                            WeatherAlert.alert_date == date.today(),
                        )
                    )
                    already_alerted = existing_alerts.scalars().all()
                    alerted_types = {a.alert_type for a in already_alerted}

                    new_alerts = evaluate_alerts(
                        forecasts=today_forecasts,
                        tasks=tasks,
                        existing_alert_types=alerted_types,
                    )

                    for alert_data in new_alerts:
                        alert = WeatherAlert(
                            project_id=project.id,
                            alert_date=date.today(),
                            **alert_data,
                        )
                        db.add(alert)

            except Exception as e:
                logger.error(f"프로젝트 {project.id} 날씨 수집 실패: {e}")
                continue

        await db.commit()
        logger.info("날씨 수집 완료")


async def _daily_evms_snapshot():
    """매일 자정 활성 프로젝트 EVMS 스냅샷 자동 저장"""
    from app.services.evms_service import compute_evms
    from app.models.evms import EVMSSnapshot

    today = date.today()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Project).where(Project.status == "active"))
        projects = result.scalars().all()
        for project in projects:
            try:
                data = await compute_evms(db, project.id, today)
                snap = EVMSSnapshot(
                    project_id=project.id,
                    snapshot_date=today,
                    total_budget=data["total_budget"],
                    planned_progress=data["planned_progress"],
                    actual_progress=data["actual_progress"],
                    pv=data["pv"], ev=data["ev"], ac=data["ac"],
                    spi=data["spi"], cpi=data["cpi"],
                    eac=data["eac"], etc=data["etc"],
                    detail_json={"tasks": data["detail"]},
                )
                db.add(snap)
            except Exception as e:
                logger.error(f"EVMS 스냅샷 실패 [{project.id}]: {e}")
        await db.commit()
    logger.info(f"EVMS 일일 스냅샷 완료: {len(projects)}개 프로젝트")


async def _morning_agent_briefings():
    """매일 오전 7시 GONGSA 아침 브리핑 자동 생성"""
    from app.models.agent import AgentConversation, AgentMessage, AgentType
    from app.models.user import User
    from app.services.agents.gongsa import gongsa_agent

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Project).where(Project.status == "active"))
        projects = result.scalars().all()

        for project in projects:
            try:
                # 프로젝트 관리자 조회 (첫 번째 admin)
                user_r = await db.execute(
                    select(User).where(User.role == "site_manager").limit(1)
                )
                user = user_r.scalar_one_or_none()
                if not user:
                    continue

                context = await gongsa_agent.build_context(db, str(project.id))
                prompt = (
                    f"오늘({context.get('today', str(date.today()))}) 아침 공정 브리핑을 작성해주세요. "
                    "날씨, 오늘 예정 공종, 주의사항을 포함해주세요."
                )
                reply = await gongsa_agent.chat(
                    messages=[{"role": "user", "content": prompt}],
                    context=context,
                )

                conv = AgentConversation(
                    project_id=project.id,
                    user_id=user.id,
                    agent_type=AgentType.GONGSA,
                    title=f"{date.today()} 아침 브리핑 (자동)",
                )
                db.add(conv)
                await db.flush()

                msg = AgentMessage(
                    conversation_id=conv.id,
                    role="assistant",
                    content=reply,
                    is_proactive=True,
                )
                db.add(msg)
            except Exception as e:
                logger.error(f"아침 브리핑 실패 [{project.id}]: {e}")

        await db.commit()
    logger.info("아침 브리핑 자동 생성 완료")


def start_scheduler():
    """FastAPI 시작 시 스케줄러를 초기화하고 시작합니다."""
    global _scheduler
    _scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    # 3시간마다 날씨 수집
    _scheduler.add_job(
        _collect_weather_for_all_projects,
        trigger=IntervalTrigger(hours=3),
        id="weather_collect",
        name="날씨 데이터 자동 수집",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # 매일 자정 EVMS 스냅샷
    _scheduler.add_job(
        _daily_evms_snapshot,
        trigger=CronTrigger(hour=0, minute=5),
        id="evms_daily",
        name="EVMS 일일 스냅샷",
        replace_existing=True,
        misfire_grace_time=600,
    )

    # 매일 오전 7시 아침 브리핑
    _scheduler.add_job(
        _morning_agent_briefings,
        trigger=CronTrigger(hour=7, minute=0),
        id="morning_briefing",
        name="GONGSA 아침 브리핑 자동 생성",
        replace_existing=True,
        misfire_grace_time=600,
    )

    _scheduler.start()
    logger.info("APScheduler 시작: 날씨(3h), EVMS 스냅샷(00:05), 아침 브리핑(07:00)")
    return _scheduler


def stop_scheduler():
    """FastAPI 종료 시 스케줄러를 중지합니다."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler 종료")
