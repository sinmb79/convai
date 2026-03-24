import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.deps import CurrentUser, DB
from app.models.settings import ClientProfile, AlertRule, WorkTypeLibrary
from app.schemas.settings import (
    ClientProfileCreate, ClientProfileResponse,
    WorkTypeCreate, WorkTypeResponse,
    AlertRuleCreate, AlertRuleResponse,
    SettingsExport,
)

router = APIRouter(prefix="/settings", tags=["커스텀 설정"])


# Client Profiles
@router.get("/client-profiles", response_model=list[ClientProfileResponse])
async def list_profiles(db: DB, current_user: CurrentUser):
    result = await db.execute(select(ClientProfile).order_by(ClientProfile.name))
    return result.scalars().all()


@router.post("/client-profiles", response_model=ClientProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(data: ClientProfileCreate, db: DB, current_user: CurrentUser):
    profile = ClientProfile(**data.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.put("/client-profiles/{profile_id}", response_model=ClientProfileResponse)
async def update_profile(profile_id: uuid.UUID, data: ClientProfileCreate, db: DB, current_user: CurrentUser):
    result = await db.execute(select(ClientProfile).where(ClientProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="발주처 프로파일을 찾을 수 없습니다")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.delete("/client-profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(profile_id: uuid.UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(ClientProfile).where(ClientProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="발주처 프로파일을 찾을 수 없습니다")
    await db.delete(profile)
    await db.commit()


# Work Types
@router.get("/work-types", response_model=list[WorkTypeResponse])
async def list_work_types(db: DB, current_user: CurrentUser):
    result = await db.execute(select(WorkTypeLibrary).order_by(WorkTypeLibrary.category, WorkTypeLibrary.name))
    return result.scalars().all()


@router.post("/work-types", response_model=WorkTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_work_type(data: WorkTypeCreate, db: DB, current_user: CurrentUser):
    wt = WorkTypeLibrary(**data.model_dump(), is_system=False)
    db.add(wt)
    await db.commit()
    await db.refresh(wt)
    return wt


# Alert Rules
@router.get("/alert-rules", response_model=list[AlertRuleResponse])
async def list_alert_rules(db: DB, current_user: CurrentUser):
    result = await db.execute(select(AlertRule).order_by(AlertRule.created_at.desc()))
    return result.scalars().all()


@router.post("/alert-rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(data: AlertRuleCreate, db: DB, current_user: CurrentUser):
    rule = AlertRule(**data.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.put("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(rule_id: uuid.UUID, data: AlertRuleCreate, db: DB, current_user: CurrentUser):
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="알림 규칙을 찾을 수 없습니다")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(rule, field, value)
    await db.commit()
    await db.refresh(rule)
    return rule


# JSON Export / Import
@router.get("/export", response_model=SettingsExport)
async def export_settings(db: DB, current_user: CurrentUser):
    profiles_result = await db.execute(select(ClientProfile))
    work_types_result = await db.execute(select(WorkTypeLibrary))
    rules_result = await db.execute(select(AlertRule))

    return SettingsExport(
        client_profiles=[ClientProfileResponse.model_validate(p) for p in profiles_result.scalars().all()],
        work_types=[WorkTypeResponse.model_validate(wt) for wt in work_types_result.scalars().all()],
        alert_rules=[AlertRuleResponse.model_validate(r) for r in rules_result.scalars().all()],
        exported_at=datetime.now(timezone.utc),
    )


@router.post("/import", status_code=status.HTTP_200_OK)
async def import_settings(data: SettingsExport, db: DB, current_user: CurrentUser):
    """Import settings from JSON. Does NOT overwrite existing records."""
    imported = {"client_profiles": 0, "work_types": 0, "alert_rules": 0}

    for profile in data.client_profiles:
        existing = await db.execute(select(ClientProfile).where(ClientProfile.name == profile.name))
        if not existing.scalar_one_or_none():
            db.add(ClientProfile(
                name=profile.name,
                report_frequency=profile.report_frequency,
                template_config=profile.template_config,
                contact_info=profile.contact_info,
                is_default=profile.is_default,
            ))
            imported["client_profiles"] += 1

    for wt in data.work_types:
        existing = await db.execute(select(WorkTypeLibrary).where(WorkTypeLibrary.code == wt.code))
        if not existing.scalar_one_or_none():
            db.add(WorkTypeLibrary(
                code=wt.code, name=wt.name, category=wt.category,
                weather_constraints=wt.weather_constraints,
                default_checklist=wt.default_checklist,
                is_system=False,
            ))
            imported["work_types"] += 1

    await db.commit()
    return {"message": "설정을 가져왔습니다", "imported": imported}
