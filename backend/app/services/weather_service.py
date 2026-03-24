"""
기상청 Open API (KMA) integration.
Fetches short-term (단기예보) and medium-term (중기예보) forecasts.
"""
import httpx
from datetime import date, datetime, timedelta, timezone
from typing import Any
from app.config import settings


KMA_BASE = settings.KMA_BASE_URL
API_KEY = settings.KMA_API_KEY

# Weather code -> Korean description
WEATHER_CODE_MAP = {
    "1": "맑음", "2": "구름조금", "3": "구름많음",
    "4": "흐림", "5": "비", "6": "비눈", "7": "눈비",
    "8": "눈",
}


async def fetch_short_term_forecast(nx: int, ny: int) -> list[dict]:
    """Fetch 단기예보 (3-day, 3-hour interval)."""
    now = datetime.now(timezone.utc).astimezone()
    # KMA issues forecasts at 02, 05, 08, 11, 14, 17, 20, 23
    base_hours = [2, 5, 8, 11, 14, 17, 20, 23]
    current_hour = now.hour
    base_hour = max([h for h in base_hours if h <= current_hour], default=23)
    base_date = now.strftime("%Y%m%d") if current_hour >= 2 else (now - timedelta(days=1)).strftime("%Y%m%d")
    base_time = f"{base_hour:02d}00"

    params = {
        "serviceKey": API_KEY,
        "pageNo": 1,
        "numOfRows": 1000,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{KMA_BASE}/getVilageFcst", params=params)
        resp.raise_for_status()
        data = resp.json()

    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    return _parse_short_term(items)


def _parse_short_term(items: list[dict]) -> list[dict]:
    """Parse KMA short-term forecast items into daily summaries."""
    daily: dict[str, dict] = {}

    for item in items:
        fcst_date = item.get("fcstDate", "")[:8]  # YYYYMMDD
        category = item.get("category", "")
        value = item.get("fcstValue", "")

        if fcst_date not in daily:
            daily[fcst_date] = {
                "date": f"{fcst_date[:4]}-{fcst_date[4:6]}-{fcst_date[6:]}",
                "temp_max": None, "temp_min": None,
                "precipitation": 0.0, "wind_speed": None,
                "sky": None, "pty": None,
            }

        d = daily[fcst_date]
        if category == "TMX" and value != "-":
            d["temp_max"] = float(value)
        elif category == "TMN" and value != "-":
            d["temp_min"] = float(value)
        elif category == "PCP" and value not in ("-", "강수없음"):
            try:
                d["precipitation"] = max(d["precipitation"], float(value.replace("mm", "").strip()))
            except ValueError:
                pass
        elif category == "WSD":
            try:
                ws = float(value)
                if d["wind_speed"] is None or ws > d["wind_speed"]:
                    d["wind_speed"] = ws
            except ValueError:
                pass
        elif category == "SKY":
            d["sky"] = value
        elif category == "PTY":
            d["pty"] = value

    result = []
    for fcst_date in sorted(daily.keys()):
        d = daily[fcst_date]
        weather_code = d.get("pty") or d.get("sky") or "1"
        result.append({
            "date": d["date"],
            "temperature_high": d["temp_max"],
            "temperature_low": d["temp_min"],
            "precipitation_mm": d["precipitation"],
            "wind_speed_ms": d["wind_speed"],
            "weather_code": weather_code,
            "weather_desc": WEATHER_CODE_MAP.get(str(weather_code), "알 수 없음"),
        })

    return result


# --- Weather Constraint Evaluation ---

# Default constraints by work type code
DEFAULT_CONSTRAINTS: dict[str, dict] = {
    "CONCRETE": {"min_temp": 5.0, "max_wind": None, "no_rain": True},
    "HIGH_WORK": {"min_temp": None, "max_wind": 10.0, "no_rain": False},
    "ASPHALT": {"min_temp": 10.0, "max_wind": None, "no_rain": True},
    "EARTHWORK": {"min_temp": None, "max_wind": None, "no_rain": True},
    "REBAR": {"min_temp": None, "max_wind": None, "no_rain": False},
}


def evaluate_weather_alerts(
    forecast: dict,
    tasks_on_date: list,
    work_type_constraints: dict[str, dict] | None = None,
) -> list[dict]:
    """
    Evaluate weather constraints for tasks on a given date.
    Returns list of alert dicts.
    """
    alerts = []
    constraints = work_type_constraints or DEFAULT_CONSTRAINTS

    for task in tasks_on_date:
        # Determine work type from task name (simple keyword matching)
        work_type = _detect_work_type(task.name)
        if not work_type or work_type not in constraints:
            continue

        constraint = constraints[work_type]
        temp_low = forecast.get("temperature_low")
        wind_speed = forecast.get("wind_speed_ms")
        precipitation = forecast.get("precipitation_mm", 0)

        # Check temperature
        if constraint.get("min_temp") and temp_low is not None:
            if temp_low < constraint["min_temp"]:
                alerts.append({
                    "task_id": str(task.id),
                    "alert_date": forecast.get("date"),
                    "alert_type": f"cold_{work_type.lower()}",
                    "severity": "critical" if temp_low < constraint["min_temp"] - 5 else "warning",
                    "message": (
                        f"[{task.name}] 최저기온 {temp_low}°C - "
                        f"{work_type} 작업 기준온도({constraint['min_temp']}°C) 미달. "
                        f"작업 조정 검토 필요."
                    ),
                })

        # Check wind
        if constraint.get("max_wind") and wind_speed is not None:
            if wind_speed > constraint["max_wind"]:
                alerts.append({
                    "task_id": str(task.id),
                    "alert_date": forecast.get("date"),
                    "alert_type": f"wind_{work_type.lower()}",
                    "severity": "critical",
                    "message": (
                        f"[{task.name}] 풍속 {wind_speed}m/s - "
                        f"허용 최대풍속({constraint['max_wind']}m/s) 초과. "
                        f"고소작업 중단 검토."
                    ),
                })

        # Check rain
        if constraint.get("no_rain") and precipitation and precipitation > 1.0:
            alerts.append({
                "task_id": str(task.id),
                "alert_date": forecast.get("date"),
                "alert_type": f"rain_{work_type.lower()}",
                "severity": "warning",
                "message": (
                    f"[{task.name}] 강수 예보 {precipitation}mm - "
                    f"{work_type} 작업 우천 시 제한. 공정 조정 검토."
                ),
            })

    return alerts


def _detect_work_type(task_name: str) -> str | None:
    """Simple keyword-based work type detection from task name."""
    name_lower = task_name.lower()
    if any(k in name_lower for k in ["콘크리트", "타설", "레미콘"]):
        return "CONCRETE"
    if any(k in name_lower for k in ["고소", "크레인", "비계", "거푸집"]):
        return "HIGH_WORK"
    if any(k in name_lower for k in ["아스팔트", "포장"]):
        return "ASPHALT"
    if any(k in name_lower for k in ["성토", "절토", "굴착", "토공"]):
        return "EARTHWORK"
    if any(k in name_lower for k in ["철근", "배근"]):
        return "REBAR"
    return None
