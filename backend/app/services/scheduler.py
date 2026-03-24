"""
APScheduler 날씨 자동 수집 배치
- 3시간마다 활성 프로젝트의 날씨 데이터를 수집
- 수집 후 날씨 경보 평가
"""
import logging
from datetime import date, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
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
        misfire_grace_time=300,  # 5분 내 누락 허용
    )

    _scheduler.start()
    logger.info("APScheduler 시작: 날씨 수집 3시간 주기")
    return _scheduler


def stop_scheduler():
    """FastAPI 종료 시 스케줄러를 중지합니다."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler 종료")
