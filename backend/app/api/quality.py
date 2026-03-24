import uuid
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func
from app.deps import CurrentUser, DB
from app.models.quality import QualityTest, QualityResult
from app.models.project import Project
from app.schemas.quality import QualityTestCreate, QualityTestUpdate, QualityTestResponse

router = APIRouter(prefix="/projects/{project_id}/quality", tags=["품질시험"])


async def _get_project_or_404(project_id: uuid.UUID, db: DB) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return p


@router.get("", response_model=list[QualityTestResponse])
async def list_quality_tests(
    project_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    test_type: str | None = None,
    result: QualityResult | None = None,
):
    query = select(QualityTest).where(QualityTest.project_id == project_id)
    if test_type:
        query = query.where(QualityTest.test_type == test_type)
    if result:
        query = query.where(QualityTest.result == result)
    query = query.order_by(QualityTest.test_date.desc())
    rows = await db.execute(query)
    return rows.scalars().all()


@router.post("", response_model=QualityTestResponse, status_code=status.HTTP_201_CREATED)
async def create_quality_test(
    project_id: uuid.UUID,
    data: QualityTestCreate,
    db: DB,
    current_user: CurrentUser,
):
    await _get_project_or_404(project_id, db)
    test = QualityTest(**data.model_dump(), project_id=project_id)
    db.add(test)
    await db.commit()
    await db.refresh(test)
    return test


@router.get("/summary")
async def quality_summary(project_id: uuid.UUID, db: DB, current_user: CurrentUser):
    """프로젝트 품질시험 합격률 요약"""
    total_q = await db.execute(
        select(func.count()).where(QualityTest.project_id == project_id)
    )
    total = total_q.scalar() or 0

    pass_q = await db.execute(
        select(func.count()).where(
            QualityTest.project_id == project_id,
            QualityTest.result == QualityResult.PASS,
        )
    )
    passed = pass_q.scalar() or 0

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total * 100, 1) if total > 0 else None,
    }


@router.get("/{test_id}", response_model=QualityTestResponse)
async def get_quality_test(
    project_id: uuid.UUID, test_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    result = await db.execute(
        select(QualityTest).where(
            QualityTest.id == test_id, QualityTest.project_id == project_id
        )
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="품질시험 기록을 찾을 수 없습니다")
    return test


@router.put("/{test_id}", response_model=QualityTestResponse)
async def update_quality_test(
    project_id: uuid.UUID,
    test_id: uuid.UUID,
    data: QualityTestUpdate,
    db: DB,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(QualityTest).where(
            QualityTest.id == test_id, QualityTest.project_id == project_id
        )
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="품질시험 기록을 찾을 수 없습니다")

    update_data = data.model_dump(exclude_none=True)

    # 측정값/기준값 변경 시 합격 여부 재계산
    new_measured = update_data.get("measured_value", test.measured_value)
    new_design = update_data.get("design_value", test.design_value)
    if "result" not in update_data and new_design is not None:
        update_data["result"] = QualityResult.PASS if new_measured >= new_design else QualityResult.FAIL

    for field, value in update_data.items():
        setattr(test, field, value)
    await db.commit()
    await db.refresh(test)
    return test


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quality_test(
    project_id: uuid.UUID, test_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    result = await db.execute(
        select(QualityTest).where(
            QualityTest.id == test_id, QualityTest.project_id == project_id
        )
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="품질시험 기록을 찾을 수 없습니다")
    await db.delete(test)
    await db.commit()
