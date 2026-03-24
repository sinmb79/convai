import uuid
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from app.deps import CurrentUser, DB
from app.models.inspection import InspectionRequest
from app.models.project import Project, WBSItem
from app.schemas.inspection import InspectionCreate, InspectionUpdate, InspectionGenerateRequest, InspectionResponse
from app.services.inspection_gen import generate_checklist
from app.services.pdf_service import generate_inspection_pdf

router = APIRouter(prefix="/projects/{project_id}/inspections", tags=["검측요청서"])


async def _get_project_or_404(project_id: uuid.UUID, db: DB) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return p


@router.get("", response_model=list[InspectionResponse])
async def list_inspections(project_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(
        select(InspectionRequest)
        .where(InspectionRequest.project_id == project_id)
        .order_by(InspectionRequest.requested_date.desc())
    )
    return result.scalars().all()


@router.post("", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED)
async def create_inspection(project_id: uuid.UUID, data: InspectionCreate, db: DB, current_user: CurrentUser):
    await _get_project_or_404(project_id, db)
    inspection = InspectionRequest(**data.model_dump(), project_id=project_id)
    db.add(inspection)
    await db.commit()
    await db.refresh(inspection)
    return inspection


@router.post("/generate", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED)
async def generate_inspection(project_id: uuid.UUID, data: InspectionGenerateRequest, db: DB, current_user: CurrentUser):
    """AI-generate inspection request checklist."""
    project = await _get_project_or_404(project_id, db)

    # Get WBS item name if provided
    wbs_name = None
    if data.wbs_item_id:
        wbs_result = await db.execute(select(WBSItem).where(WBSItem.id == data.wbs_item_id))
        wbs = wbs_result.scalar_one_or_none()
        if wbs:
            wbs_name = wbs.name

    checklist = await generate_checklist(
        project_name=project.name,
        inspection_type=data.inspection_type,
        location_detail=data.location_detail,
        requested_date=str(data.requested_date),
        wbs_name=wbs_name,
    )

    inspection = InspectionRequest(
        project_id=project_id,
        wbs_item_id=data.wbs_item_id,
        inspection_type=data.inspection_type,
        requested_date=data.requested_date,
        location_detail=data.location_detail,
        checklist_items=checklist,
        ai_generated=True,
    )
    db.add(inspection)
    await db.commit()
    await db.refresh(inspection)
    return inspection


@router.get("/{inspection_id}", response_model=InspectionResponse)
async def get_inspection(project_id: uuid.UUID, inspection_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(InspectionRequest).where(InspectionRequest.id == inspection_id, InspectionRequest.project_id == project_id))
    insp = result.scalar_one_or_none()
    if not insp:
        raise HTTPException(status_code=404, detail="검측요청서를 찾을 수 없습니다")
    return insp


@router.put("/{inspection_id}", response_model=InspectionResponse)
async def update_inspection(project_id: uuid.UUID, inspection_id: uuid.UUID, data: InspectionUpdate, db: DB, current_user: CurrentUser):
    result = await db.execute(select(InspectionRequest).where(InspectionRequest.id == inspection_id, InspectionRequest.project_id == project_id))
    insp = result.scalar_one_or_none()
    if not insp:
        raise HTTPException(status_code=404, detail="검측요청서를 찾을 수 없습니다")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(insp, field, value)
    await db.commit()
    await db.refresh(insp)
    return insp


@router.get("/{inspection_id}/pdf")
async def download_inspection_pdf(project_id: uuid.UUID, inspection_id: uuid.UUID, db: DB, current_user: CurrentUser):
    """검측요청서 PDF 다운로드"""
    r = await db.execute(select(InspectionRequest).where(InspectionRequest.id == inspection_id, InspectionRequest.project_id == project_id))
    insp = r.scalar_one_or_none()
    if not insp:
        raise HTTPException(status_code=404, detail="검측요청서를 찾을 수 없습니다")
    project = await _get_project_or_404(project_id, db)
    pdf_bytes = generate_inspection_pdf(insp, project)
    filename = f"inspection_{insp.requested_date}_{insp.inspection_type}.pdf"
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"})


@router.delete("/{inspection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inspection(project_id: uuid.UUID, inspection_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(InspectionRequest).where(InspectionRequest.id == inspection_id, InspectionRequest.project_id == project_id))
    insp = result.scalar_one_or_none()
    if not insp:
        raise HTTPException(status_code=404, detail="검측요청서를 찾을 수 없습니다")
    await db.delete(insp)
    await db.commit()
