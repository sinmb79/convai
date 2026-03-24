"""Tests for weather service."""
import pytest
from unittest.mock import MagicMock
import uuid
from app.services.weather_service import evaluate_weather_alerts, _detect_work_type, _parse_short_term


def make_task(name: str) -> MagicMock:
    t = MagicMock()
    t.id = uuid.uuid4()
    t.name = name
    return t


def test_detect_work_type_concrete():
    assert _detect_work_type("콘크리트 타설") == "CONCRETE"
    assert _detect_work_type("레미콘 타설 공사") == "CONCRETE"


def test_detect_work_type_high_work():
    assert _detect_work_type("고소 작업") == "HIGH_WORK"
    assert _detect_work_type("비계 설치") == "HIGH_WORK"


def test_detect_work_type_unknown():
    assert _detect_work_type("기타 공사") is None


def test_evaluate_cold_concrete_alert():
    task = make_task("콘크리트 타설")
    forecast = {
        "date": "2026-04-01",
        "temperature_low": 3.0,
        "wind_speed_ms": 2.0,
        "precipitation_mm": 0.0,
    }
    alerts = evaluate_weather_alerts(forecast, [task])
    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "cold_concrete"
    assert alerts[0]["severity"] == "warning"


def test_evaluate_rain_concrete_alert():
    task = make_task("콘크리트 타설")
    forecast = {
        "date": "2026-04-01",
        "temperature_low": 15.0,
        "wind_speed_ms": 2.0,
        "precipitation_mm": 5.0,
    }
    alerts = evaluate_weather_alerts(forecast, [task])
    assert any(a["alert_type"] == "rain_concrete" for a in alerts)


def test_no_alert_good_weather():
    task = make_task("콘크리트 타설")
    forecast = {
        "date": "2026-04-01",
        "temperature_low": 15.0,
        "wind_speed_ms": 3.0,
        "precipitation_mm": 0.0,
    }
    alerts = evaluate_weather_alerts(forecast, [task])
    assert len(alerts) == 0


def test_wind_alert_high_work():
    task = make_task("고소 작업 비계")
    forecast = {
        "date": "2026-04-01",
        "temperature_low": 10.0,
        "wind_speed_ms": 12.0,
        "precipitation_mm": 0.0,
    }
    alerts = evaluate_weather_alerts(forecast, [task])
    assert any(a["alert_type"] == "wind_high_work" for a in alerts)
