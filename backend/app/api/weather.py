import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.deps import CurrentUser, DB
from app.models.project import Project
from app.models.weather import WeatherData, WeatherAlert, ForecastType
from app.models.task import Task
from app.schemas.weather import WeatherDataResponse, WeatherAlertResponse, WeatherForecastSummary
from app.services.weather_service import fetch_short_term_forecast, evaluate_weather_alerts

router = APIRouter(prefix="/projects/{project_id}/weather", tags=["날씨 연동"])


async def _get_project_or_404(project_id: uuid.UUID, db: DB) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return p


@router.get("", response_model=WeatherForecastSummary)
async def get_weather(project_id: uuid.UUID, db: DB, current_user: CurrentUser):
    """Get weather forecast and active alerts for a project."""
    from datetime import date
    today = date.today()

    forecast_result = await db.execute(
        select(WeatherData)
        .where(WeatherData.project_id == project_id, WeatherData.forecast_date >= today)
        .order_by(WeatherData.forecast_date)
    )
    forecast = forecast_result.scalars().all()

    alerts_result = await db.execute(
        select(WeatherAlert)
        .where(WeatherAlert.project_id == project_id, WeatherAlert.alert_date >= today, WeatherAlert.is_acknowledged == False)
        .order_by(WeatherAlert.alert_date)
    )
    alerts = alerts_result.scalars().all()

    return WeatherForecastSummary(
        forecast=[WeatherDataResponse.model_validate(f) for f in forecast],
        active_alerts=[WeatherAlertResponse.model_validate(a) for a in alerts],
    )


@router.post("/refresh")
async def refresh_weather(project_id: uuid.UUID, db: DB, current_user: CurrentUser):
    """Fetch fresh weather data from KMA and evaluate alerts."""
    project = await _get_project_or_404(project_id, db)

    if not project.weather_grid_x or not project.weather_grid_y:
        raise HTTPException(status_code=400, detail="프로젝트에 위치 정보(위경도)가 설정되지 않았습니다")

    forecasts = await fetch_short_term_forecast(project.weather_grid_x, project.weather_grid_y)

    # Save/update weather data
    for fc in forecasts:
        from datetime import date
        fc_date = date.fromisoformat(fc["date"])

        existing = await db.execute(
            select(WeatherData).where(
                WeatherData.project_id == project_id,
                WeatherData.forecast_date == fc_date,
                WeatherData.forecast_type == ForecastType.SHORT_TERM,
            )
        )
        wd = existing.scalar_one_or_none()
        if not wd:
            wd = WeatherData(project_id=project_id, forecast_type=ForecastType.SHORT_TERM)
            db.add(wd)

        wd.forecast_date = fc_date
        wd.temperature_high = fc.get("temperature_high")
        wd.temperature_low = fc.get("temperature_low")
        wd.precipitation_mm = fc.get("precipitation_mm")
        wd.wind_speed_ms = fc.get("wind_speed_ms")
        wd.weather_code = fc.get("weather_code")
        wd.raw_data = fc
        wd.fetched_at = datetime.now(timezone.utc)

    # Get tasks in upcoming forecast period
    from datetime import timedelta
    start_date = date.today()
    end_date = start_date + timedelta(days=len(forecasts))
    tasks_result = await db.execute(
        select(Task).where(
            Task.project_id == project_id,
            Task.planned_start >= start_date,
            Task.planned_start <= end_date,
        )
    )
    upcoming_tasks = tasks_result.scalars().all()

    # Evaluate and save alerts
    for fc in forecasts:
        from datetime import date as date_type
        fc_date_obj = date_type.fromisoformat(fc["date"])
        tasks_on_date = [t for t in upcoming_tasks if t.planned_start and t.planned_start <= fc_date_obj <= (t.planned_end or fc_date_obj)]
        new_alerts = evaluate_weather_alerts(fc, tasks_on_date)

        for alert_data in new_alerts:
            existing_alert = await db.execute(
                select(WeatherAlert).where(
                    WeatherAlert.project_id == project_id,
                    WeatherAlert.alert_date == fc_date_obj,
                    WeatherAlert.alert_type == alert_data["alert_type"],
                )
            )
            if not existing_alert.scalar_one_or_none():
                alert = WeatherAlert(
                    project_id=project_id,
                    task_id=uuid.UUID(alert_data["task_id"]) if alert_data.get("task_id") else None,
                    alert_date=fc_date_obj,
                    alert_type=alert_data["alert_type"],
                    severity=alert_data["severity"],
                    message=alert_data["message"],
                )
                db.add(alert)

    await db.commit()
    return {"message": f"날씨 정보가 업데이트되었습니다 ({len(forecasts)}일치)"}


@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(project_id: uuid.UUID, alert_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(WeatherAlert).where(WeatherAlert.id == alert_id, WeatherAlert.project_id == project_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="경보를 찾을 수 없습니다")
    alert.is_acknowledged = True
    await db.commit()
    return {"message": "경보가 확인 처리되었습니다"}
