import uuid
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.deps import CurrentUser, DB
from app.models.task import Task, TaskDependency
from app.models.project import Project
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskDependencyCreate, GanttData
from app.services.gantt import compute_cpm

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["공정관리 (Gantt)"])


async def _get_project_or_404(project_id: uuid.UUID, db: DB):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return project


@router.get("", response_model=list[TaskResponse])
async def list_tasks(project_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Task).where(Task.project_id == project_id).order_by(Task.sort_order))
    return result.scalars().all()


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(project_id: uuid.UUID, data: TaskCreate, db: DB, current_user: CurrentUser):
    await _get_project_or_404(project_id, db)
    task = Task(**data.model_dump(), project_id=project_id)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("/gantt", response_model=GanttData)
async def get_gantt(project_id: uuid.UUID, db: DB, current_user: CurrentUser):
    """Returns tasks with CPM computed values."""
    tasks_result = await db.execute(select(Task).where(Task.project_id == project_id).order_by(Task.sort_order))
    tasks = tasks_result.scalars().all()

    deps_result = await db.execute(
        select(TaskDependency).where(
            TaskDependency.predecessor_id.in_([t.id for t in tasks])
        )
    )
    deps = deps_result.scalars().all()

    # Run CPM
    cpm_result = compute_cpm(tasks, deps)
    if cpm_result and isinstance(cpm_result, tuple):
        cpm_data, project_duration = cpm_result
    else:
        cpm_data, project_duration = {}, None

    # Update tasks with CPM results
    critical_ids = []
    for task in tasks:
        if task.id in cpm_data:
            data = cpm_data[task.id]
            task.early_start = data["early_start"]
            task.early_finish = data["early_finish"]
            task.late_start = data["late_start"]
            task.late_finish = data["late_finish"]
            task.total_float = data["total_float"]
            task.is_critical = data["is_critical"]
            if data["is_critical"]:
                critical_ids.append(task.id)

    await db.commit()

    return GanttData(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        critical_path=critical_ids,
        project_duration_days=project_duration,
    )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(project_id: uuid.UUID, task_id: uuid.UUID, data: TaskUpdate, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.project_id == project_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="태스크를 찾을 수 없습니다")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(project_id: uuid.UUID, task_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.project_id == project_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="태스크를 찾을 수 없습니다")
    await db.delete(task)
    await db.commit()


@router.post("/{task_id}/dependencies", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_dependency(project_id: uuid.UUID, task_id: uuid.UUID, data: TaskDependencyCreate, db: DB, current_user: CurrentUser):
    dep = TaskDependency(
        predecessor_id=data.predecessor_id,
        successor_id=data.successor_id,
        dependency_type=data.dependency_type,
        lag_days=data.lag_days,
    )
    db.add(dep)
    await db.commit()
    return {"message": "의존관계가 추가되었습니다"}


@router.delete("/{task_id}/dependencies/{dep_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dependency(project_id: uuid.UUID, task_id: uuid.UUID, dep_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(TaskDependency).where(TaskDependency.id == dep_id))
    dep = result.scalar_one_or_none()
    if not dep:
        raise HTTPException(status_code=404, detail="의존관계를 찾을 수 없습니다")
    await db.delete(dep)
    await db.commit()
