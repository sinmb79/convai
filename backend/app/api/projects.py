import uuid
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.deps import CurrentUser, DB
from app.models.project import Project, WBSItem
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, WBSItemCreate, WBSItemResponse

router = APIRouter(prefix="/projects", tags=["프로젝트"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(db: DB, current_user: CurrentUser):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(data: ProjectCreate, db: DB, current_user: CurrentUser):
    # Check for duplicate code
    existing = await db.execute(select(Project).where(Project.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"프로젝트 코드 '{data.code}'가 이미 존재합니다")

    project = Project(**data.model_dump(), owner_id=current_user.id)

    # Auto-compute KMA grid from lat/lng
    if data.location_lat and data.location_lng:
        grid_x, grid_y = _latlon_to_kma_grid(data.location_lat, data.location_lng)
        project.weather_grid_x = grid_x
        project.weather_grid_y = grid_y

    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: uuid.UUID, data: ProjectUpdate, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(project, field, value)

    # Recompute grid if location changed
    if (data.location_lat or data.location_lng) and project.location_lat and project.location_lng:
        grid_x, grid_y = _latlon_to_kma_grid(project.location_lat, project.location_lng)
        project.weather_grid_x = grid_x
        project.weather_grid_y = grid_y

    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    await db.delete(project)
    await db.commit()


# WBS endpoints
@router.get("/{project_id}/wbs", response_model=list[WBSItemResponse])
async def get_wbs(project_id: uuid.UUID, db: DB, current_user: CurrentUser):
    """Return WBS tree (top-level items with nested children)."""
    result = await db.execute(
        select(WBSItem)
        .where(WBSItem.project_id == project_id, WBSItem.parent_id == None)
        .options(selectinload(WBSItem.children).selectinload(WBSItem.children))
        .order_by(WBSItem.sort_order)
    )
    return result.scalars().all()


@router.post("/{project_id}/wbs", response_model=WBSItemResponse, status_code=status.HTTP_201_CREATED)
async def create_wbs_item(project_id: uuid.UUID, data: WBSItemCreate, db: DB, current_user: CurrentUser):
    item = WBSItem(**data.model_dump(), project_id=project_id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/{project_id}/wbs/{item_id}", response_model=WBSItemResponse)
async def update_wbs_item(project_id: uuid.UUID, item_id: uuid.UUID, data: WBSItemCreate, db: DB, current_user: CurrentUser):
    result = await db.execute(select(WBSItem).where(WBSItem.id == item_id, WBSItem.project_id == project_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="WBS 항목을 찾을 수 없습니다")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{project_id}/wbs/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wbs_item(project_id: uuid.UUID, item_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(WBSItem).where(WBSItem.id == item_id, WBSItem.project_id == project_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="WBS 항목을 찾을 수 없습니다")
    await db.delete(item)
    await db.commit()


def _latlon_to_kma_grid(lat: float, lng: float) -> tuple[int, int]:
    """Convert latitude/longitude to KMA forecast grid coordinates (Lambert Conformal Conic)."""
    import math
    RE = 6371.00877  # Earth radius (km)
    GRID = 5.0        # Grid spacing (km)
    SLAT1 = 30.0      # Standard latitude 1
    SLAT2 = 60.0      # Standard latitude 2
    OLON = 126.0      # Reference longitude
    OLAT = 38.0       # Reference latitude
    XO = 43           # Reference X
    YO = 136          # Reference Y

    DEGRAD = math.pi / 180.0
    re = RE / GRID
    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD
    olon = OLON * DEGRAD
    olat = OLAT * DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = (sf ** sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / (ro ** sn)

    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / (ra ** sn)
    theta = lng * DEGRAD - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    x = int(ra * math.sin(theta) + XO + 0.5)
    y = int(ro - ra * math.cos(theta) + YO + 0.5)
    return x, y
