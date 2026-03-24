"""
CPM (Critical Path Method) calculation for Gantt chart.
"""
from datetime import date, timedelta
from typing import NamedTuple
import uuid


class TaskNode(NamedTuple):
    id: uuid.UUID
    planned_start: date | None
    planned_end: date | None
    duration_days: int


def compute_cpm(tasks: list, dependencies: list) -> dict[uuid.UUID, dict]:
    """
    Compute CPM forward/backward pass.
    Returns dict: task_id -> {early_start, early_finish, late_start, late_finish, total_float, is_critical}
    """
    if not tasks:
        return {}

    # Build adjacency maps
    task_map = {t.id: t for t in tasks}
    successors: dict[uuid.UUID, list[uuid.UUID]] = {t.id: [] for t in tasks}
    predecessors: dict[uuid.UUID, list[uuid.UUID]] = {t.id: [] for t in tasks}

    for dep in dependencies:
        successors[dep.predecessor_id].append(dep.successor_id)
        predecessors[dep.successor_id].append(dep.predecessor_id)

    def get_duration(task) -> int:
        if task.planned_start and task.planned_end:
            return max(1, (task.planned_end - task.planned_start).days + 1)
        return 1

    # Topological sort (Kahn's algorithm)
    in_degree = {t.id: len(predecessors[t.id]) for t in tasks}
    queue = [t.id for t in tasks if in_degree[t.id] == 0]
    topo_order = []

    while queue:
        node = queue.pop(0)
        topo_order.append(node)
        for succ in successors[node]:
            in_degree[succ] -= 1
            if in_degree[succ] == 0:
                queue.append(succ)

    # Forward pass: compute Early Start (ES) and Early Finish (EF)
    es: dict[uuid.UUID, int] = {}  # days from project start
    ef: dict[uuid.UUID, int] = {}

    for tid in topo_order:
        task = task_map[tid]
        dur = get_duration(task)
        if not predecessors[tid]:
            es[tid] = 0
        else:
            es[tid] = max(ef[p] for p in predecessors[tid])
        ef[tid] = es[tid] + dur

    if not ef:
        return {}

    project_duration = max(ef.values())

    # Backward pass: compute Late Finish (LF) and Late Start (LS)
    lf: dict[uuid.UUID, int] = {}
    ls: dict[uuid.UUID, int] = {}

    for tid in reversed(topo_order):
        task = task_map[tid]
        dur = get_duration(task)
        if not successors[tid]:
            lf[tid] = project_duration
        else:
            lf[tid] = min(ls[s] for s in successors[tid])
        ls[tid] = lf[tid] - dur

    # Compute float and critical path
    result = {}
    # Find an actual project start date
    project_start = None
    for t in tasks:
        if t.planned_start:
            if project_start is None or t.planned_start < project_start:
                project_start = t.planned_start
    if not project_start:
        project_start = date.today()

    for tid in topo_order:
        total_float = ls[tid] - es[tid]
        is_critical = total_float == 0

        early_start_date = project_start + timedelta(days=es[tid])
        early_finish_date = project_start + timedelta(days=ef[tid] - 1)
        late_start_date = project_start + timedelta(days=ls[tid])
        late_finish_date = project_start + timedelta(days=lf[tid] - 1)

        result[tid] = {
            "early_start": early_start_date,
            "early_finish": early_finish_date,
            "late_start": late_start_date,
            "late_finish": late_finish_date,
            "total_float": total_float,
            "is_critical": is_critical,
        }

    return result, project_duration
