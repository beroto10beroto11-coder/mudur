import json
import random
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.database import get_db
from app.models.duty import Duty
from app.models.teacher import Teacher
from app.models.timetable import TimetableLesson, Timetable
from app.models.settings import SystemSetting
from app.schemas.duty import DutyAutoAssignRequest, DutyCreate, DutyResponse

router = APIRouter(prefix="/duties", tags=["Duties"])

DEFAULT_LOCATIONS = ["1. Kat Koridor", "2. Kat Koridor", "Bahçe", "Kantin Katı", "Spor Salonu"]


class DutyUpdateRequest(BaseModel):
    teacher_id: int | None = None
    day: int | None = None
    location: str | None = None
    notes: str | None = None


class LocationsUpdateRequest(BaseModel):
    locations: list[str]


@router.get("/locations", response_model=list[str])
async def get_duty_locations(
    school_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    res = await db.execute(
        select(SystemSetting).where(
            SystemSetting.school_id == school_id,
            SystemSetting.key == "duty_locations",
        )
    )
    setting = res.scalar_one_or_none()
    if setting and setting.value:
        try:
            return json.loads(setting.value)
        except Exception:
            pass
    return DEFAULT_LOCATIONS


@router.post("/locations", response_model=list[str])
async def save_duty_locations(
    school_id: int,
    data: LocationsUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    res = await db.execute(
        select(SystemSetting).where(
            SystemSetting.school_id == school_id,
            SystemSetting.key == "duty_locations",
        )
    )
    setting = res.scalar_one_or_none()
    locs_json = json.dumps(data.locations, ensure_ascii=False)

    if not setting:
        setting = SystemSetting(
            school_id=school_id,
            key="duty_locations",
            value=locs_json,
            description="Nöbet yerleri listesi",
        )
        db.add(setting)
    else:
        setting.value = locs_json

    await db.commit()
    return data.locations


@router.get("", response_model=list[DutyResponse])
async def list_duties(
    school_id: int,
    academic_year_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    query = select(Duty).where(
        Duty.school_id == school_id,
        Duty.academic_year_id == academic_year_id,
    ).order_by(Duty.day, Duty.location)
    result = await db.execute(query)
    duties = list(result.scalars().all())

    teachers_res = await db.execute(select(Teacher).where(Teacher.school_id == school_id))
    t_map = {t.id: t.full_name for t in teachers_res.scalars().all()}

    response_list = []
    for d in duties:
        item = DutyResponse.model_validate(d)
        item.teacher_name = t_map.get(d.teacher_id)
        response_list.append(item)

    return response_list


@router.post("", response_model=DutyResponse, status_code=status.HTTP_201_CREATED)
async def create_duty(
    school_id: int,
    data: DutyCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    duty = Duty(school_id=school_id, **data.model_dump())
    db.add(duty)
    await db.commit()
    await db.refresh(duty)
    return duty


@router.put("/{duty_id}", response_model=DutyResponse)
async def update_duty(
    duty_id: int,
    data: DutyUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    res = await db.execute(select(Duty).where(Duty.id == duty_id))
    duty = res.scalar_one_or_none()
    if not duty:
        raise HTTPException(status_code=404, detail="Nöbet kaydı bulunamadı.")

    if data.teacher_id is not None:
        duty.teacher_id = data.teacher_id
    if data.day is not None:
        duty.day = data.day
    if data.location is not None:
        duty.location = data.location
    if data.notes is not None:
        duty.notes = data.notes

    duty.automatic = False  # Mark as manually edited

    await db.commit()
    await db.refresh(duty)

    t_res = await db.execute(select(Teacher).where(Teacher.id == duty.teacher_id))
    t = t_res.scalar_one_or_none()
    item = DutyResponse.model_validate(duty)
    item.teacher_name = t.full_name if t else None
    return item


@router.delete("/{duty_id}", status_code=status.HTTP_200_OK)
async def delete_duty(
    duty_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    res = await db.execute(select(Duty).where(Duty.id == duty_id))
    duty = res.scalar_one_or_none()
    if not duty:
        raise HTTPException(status_code=404, detail="Nöbet kaydı bulunamadı.")

    await db.delete(duty)
    await db.commit()
    return {"message": "Nöbet kaydı silindi."}


@router.post("/auto-assign", response_model=list[DutyResponse])
async def auto_assign_duties(
    school_id: int,
    data: DutyAutoAssignRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    # Fetch active teachers
    t_res = await db.execute(select(Teacher).where(Teacher.school_id == school_id, Teacher.is_active == True))
    teachers = list(t_res.scalars().all())

    if not teachers:
        return []

    # Map teachers' teaching days from active timetable
    t_days: dict[int, set[int]] = {t.id: set() for t in teachers}
    tt_res = await db.execute(
        select(Timetable)
        .where(Timetable.school_id == school_id, Timetable.academic_year_id == data.academic_year_id)
        .order_by(Timetable.created_at.desc())
        .limit(1)
    )
    latest_tt = tt_res.scalar_one_or_none()

    if latest_tt:
        lessons_res = await db.execute(select(TimetableLesson).where(TimetableLesson.timetable_id == latest_tt.id))
        for l in lessons_res.scalars().all():
            if l.teacher_id in t_days:
                t_days[l.teacher_id].add(l.day)

    # Clear old automatic duties
    await db.execute(
        delete(Duty).where(
            Duty.school_id == school_id,
            Duty.academic_year_id == data.academic_year_id,
            Duty.automatic == True,
        )
    )

    locations = data.locations if data.locations else DEFAULT_LOCATIONS
    assigned_duties = []
    duty_counts: dict[int, int] = {t.id: 0 for t in teachers}

    for day in data.days:
        day_assigned_teachers: set[int] = set()

        for loc in locations:
            # Candidate teachers: teach on this day, no duty on this day yet, sorted by lowest total duty count
            candidates = [
                t for t in teachers
                if t.id not in day_assigned_teachers and (not t_days[t.id] or day in t_days[t.id])
            ]
            if not candidates:
                candidates = [t for t in teachers if t.id not in day_assigned_teachers]

            if not candidates:
                continue

            candidates.sort(key=lambda t: (duty_counts[t.id], random.random()))
            selected_teacher = candidates[0]

            duty = Duty(
                school_id=school_id,
                academic_year_id=data.academic_year_id,
                teacher_id=selected_teacher.id,
                day=day,
                location=loc,
                automatic=True,
            )
            db.add(duty)
            assigned_duties.append(duty)

            day_assigned_teachers.add(selected_teacher.id)
            duty_counts[selected_teacher.id] += 1

    await db.commit()

    # Preload teacher names for response
    t_map = {t.id: t.full_name for t in teachers}
    response_list = []
    for d in assigned_duties:
        item = DutyResponse.model_validate(d)
        item.teacher_name = t_map.get(d.teacher_id)
        response_list.append(item)

    return response_list
