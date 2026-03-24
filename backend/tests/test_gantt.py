"""Tests for CPM Gantt calculation."""
import pytest
from datetime import date
from unittest.mock import MagicMock
import uuid
from app.services.gantt import compute_cpm


def make_task(name: str, start: str, end: str) -> MagicMock:
    t = MagicMock()
    t.id = uuid.uuid4()
    t.name = name
    t.planned_start = date.fromisoformat(start)
    t.planned_end = date.fromisoformat(end)
    return t


def make_dep(pred_id, succ_id) -> MagicMock:
    d = MagicMock()
    d.predecessor_id = pred_id
    d.successor_id = succ_id
    return d


def test_cpm_no_dependencies():
    tasks = [
        make_task("A", "2026-04-01", "2026-04-05"),
        make_task("B", "2026-04-01", "2026-04-10"),
    ]
    result = compute_cpm(tasks, [])
    assert isinstance(result, tuple)
    cpm_data, duration = result
    assert len(cpm_data) == 2
    assert duration > 0


def test_cpm_serial_tasks():
    t1 = make_task("A", "2026-04-01", "2026-04-05")
    t2 = make_task("B", "2026-04-06", "2026-04-10")
    dep = make_dep(t1.id, t2.id)

    result = compute_cpm([t1, t2], [dep])
    assert isinstance(result, tuple)
    cpm_data, duration = result

    # Serial tasks: both should be critical
    assert cpm_data[t1.id]["is_critical"] is True
    assert cpm_data[t2.id]["is_critical"] is True


def test_cpm_parallel_tasks():
    """In parallel paths, only the longer path is critical."""
    t_start = make_task("Start", "2026-04-01", "2026-04-02")
    t_long = make_task("Long Path", "2026-04-03", "2026-04-20")  # 18 days
    t_short = make_task("Short Path", "2026-04-03", "2026-04-10")  # 8 days
    t_end = make_task("End", "2026-04-21", "2026-04-22")

    deps = [
        make_dep(t_start.id, t_long.id),
        make_dep(t_start.id, t_short.id),
        make_dep(t_long.id, t_end.id),
        make_dep(t_short.id, t_end.id),
    ]

    result = compute_cpm([t_start, t_long, t_short, t_end], deps)
    assert isinstance(result, tuple)
    cpm_data, duration = result

    # Long path and start/end should be critical; short path should not
    assert cpm_data[t_long.id]["is_critical"] is True
    assert cpm_data[t_short.id]["is_critical"] is False


def test_cpm_empty_tasks():
    result = compute_cpm([], [])
    assert result == {}
