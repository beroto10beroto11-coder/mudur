import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.core.database import get_db, AsyncSessionLocal
from app.core.redis import get_redis
from app.models.assignment import CourseAssignment
from app.models.class_ import ClassGroup
from app.models.classroom import Classroom
from app.models.course import Course
from app.models.teacher import Teacher, TeacherAvailability
from app.models.timetable import Timetable, TimetableLesson, TimetableStatus, TimetableVersion
from app.models.timeslot import TimeSlot
from app.schemas.timetable import (
    TimetableGenerateRequest,
    TimetableLessonMoveRequest,
    TimetableLessonResponse,
    TimetableResponse,
    TimetableVersionResponse,
)
from app.tasks.solver_task import (
    run_solver,
    _build_scheduler_input,
)
from app.solver.scheduler.validator import validate_feasibility

router = APIRouter(prefix="/timetables", tags=["Timetables"])


@router.get("/validate", tags=["Timetables"])
async def validate_timetable_feasibility(
    school_id: int,
    academic_year_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """
    Solver çalıştırmadan önce ön-doğrulama yapar.
    Kapasite yetersizliği ve saat dengesizliği raporlarını döndürür.
    Kritik ihlal yoksa solver çalıştırılabilir.
    """
    teachers_res = await db.execute(
        select(Teacher).where(Teacher.school_id == school_id, Teacher.is_active == True)
    )
    teachers = list(teachers_res.scalars().all())

    classes_res = await db.execute(
        select(ClassGroup).where(ClassGroup.school_id == school_id, ClassGroup.is_active == True)
    )
    classes = list(classes_res.scalars().all())

    asgns_res = await db.execute(
        select(CourseAssignment)
        .options(selectinload(CourseAssignment.course))
        .where(
            CourseAssignment.school_id == school_id,
            CourseAssignment.academic_year_id == academic_year_id,
            CourseAssignment.is_active == True,
        )
    )
    assignments = list(asgns_res.scalars().all())

    slots_res = await db.execute(
        select(TimeSlot).where(
            TimeSlot.academic_year_id == academic_year_id,
            TimeSlot.is_active == True,
        )
    )
    timeslots = list(slots_res.scalars().all())

    avail_res = await db.execute(
        select(TeacherAvailability).where(TeacherAvailability.academic_year_id == academic_year_id)
    )
    availabilities = list(avail_res.scalars().all())

    try:
        scheduler_input = _build_scheduler_input(
            teachers=teachers,
            classes=classes,
            assignments=assignments,
            timeslots=timeslots,
            availabilities=availabilities,
            school_id=school_id,
        )
        ihlaller = validate_feasibility(scheduler_input)
    except Exception as e:
        return {
            "gecerli": False,
            "hata": str(e),
            "ihlaller": [],
        }

    kritik = [ih for ih in ihlaller if ih.tur == "YETERSIZ_OGRETMEN"]
    return {
        "gecerli": len(kritik) == 0,
        "kritik_ihlal_sayisi": len(kritik),
        "uyari_sayisi": len(ihlaller) - len(kritik),
        "ihlaller": [
            {
                "tur": ih.tur,
                "mesaj": ih.mesaj,
                "detay": ih.detay,
            }
            for ih in ihlaller
        ],
    }


@router.get("", response_model=list[TimetableResponse])
async def list_timetables(
    school_id: int,
    academic_year_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    from sqlalchemy import func as sa_func
    query = select(Timetable).where(
        Timetable.school_id == school_id,
        Timetable.academic_year_id == academic_year_id,
        Timetable.is_active == True,
    )
    result = await db.execute(query)
    timetables = list(result.scalars().all())

    # Enrich with real lessons_count
    for tt in timetables:
        count_res = await db.execute(
            select(sa_func.count()).where(TimetableLesson.timetable_id == tt.id)
        )
        tt.lessons_count = count_res.scalar_one()

    return timetables


@router.post("/generate", response_model=TimetableResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_timetable(
    school_id: int,
    data: TimetableGenerateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    import asyncio
    import threading

    timetable = Timetable(
        school_id=school_id,
        academic_year_id=data.academic_year_id,
        name=data.name,
        status=TimetableStatus.GENERATING,
    )
    db.add(timetable)
    await db.commit()
    await db.refresh(timetable)
    tt_id = timetable.id

    celery_ok = False
    try:
        # apply_async ile timeout: Redis yoksa 2sn sonra exception -> thread fallback
        task = run_solver.apply_async(
            args=[tt_id, school_id, data.academic_year_id],
            expires=3600,
            time_limit=300,
        )
        timetable.solver_job_id = task.id
        celery_ok = True
    except Exception:
        pass

    if not celery_ok:
        # Run solver in a background daemon thread (no Celery/Redis needed)
        from app.tasks.solver_task import _execute_solver

        def _run_in_thread():
            asyncio.run(_execute_solver(tt_id, school_id, data.academic_year_id))

        thread = threading.Thread(target=_run_in_thread, daemon=True)
        thread.start()
        timetable.solver_job_id = f"thread_job_{tt_id}"

    await db.commit()
    await db.refresh(timetable)
    return timetable


@router.get("/{timetable_id}", response_model=TimetableResponse)
async def get_timetable(
    timetable_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    from sqlalchemy import func as sa_func
    result = await db.execute(select(Timetable).where(Timetable.id == timetable_id))
    timetable = result.scalar_one_or_none()
    if not timetable:
        raise HTTPException(status_code=404, detail="Ders programı bulunamadı.")
    count_res = await db.execute(
        select(sa_func.count()).where(TimetableLesson.timetable_id == timetable_id)
    )
    timetable.lessons_count = count_res.scalar_one()
    return timetable


@router.get("/{timetable_id}/lessons", response_model=list[TimetableLessonResponse])
async def get_timetable_lessons(
    timetable_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    teacher_id: int | None = None,
    class_id: int | None = None,
    classroom_id: int | None = None,
):
    query = select(TimetableLesson).where(TimetableLesson.timetable_id == timetable_id)
    if teacher_id:
        query = query.where(TimetableLesson.teacher_id == teacher_id)
    if class_id:
        query = query.where(TimetableLesson.class_id == class_id)
    if classroom_id:
        query = query.where(TimetableLesson.classroom_id == classroom_id)

    result = await db.execute(query)
    lessons = list(result.scalars().all())

    # Pre-fetch lookup dicts for display names
    teachers_res = await db.execute(select(Teacher))
    teacher_map = {t.id: t.full_name for t in teachers_res.scalars().all()}

    courses_res = await db.execute(select(Course))
    course_map = {c.id: c.name for c in courses_res.scalars().all()}

    classes_res = await db.execute(select(ClassGroup))
    class_map = {c.id: c.name for c in classes_res.scalars().all()}

    rooms_res = await db.execute(select(Classroom))
    room_map = {r.id: r.name for r in rooms_res.scalars().all()}

    response_list = []
    for l in lessons:
        item = TimetableLessonResponse.model_validate(l)
        item.teacher_name = teacher_map.get(l.teacher_id)
        item.course_name = course_map.get(l.course_id)
        item.class_name = class_map.get(l.class_id)
        item.classroom_name = room_map.get(l.classroom_id) if l.classroom_id else None
        response_list.append(item)

    return response_list


@router.patch("/{timetable_id}/lessons/{lesson_id}", response_model=TimetableLessonResponse)
async def move_lesson(
    timetable_id: int,
    lesson_id: int,
    data: TimetableLessonMoveRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    result = await db.execute(
        select(TimetableLesson).where(
            TimetableLesson.id == lesson_id,
            TimetableLesson.timetable_id == timetable_id,
        )
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Ders bulunamadı.")

    # 1. Validation check for conflicts
    # Teacher conflict
    t_conflict = await db.execute(
        select(TimetableLesson).where(
            TimetableLesson.timetable_id == timetable_id,
            TimetableLesson.teacher_id == lesson.teacher_id,
            TimetableLesson.day == data.new_day,
            TimetableLesson.period == data.new_period,
            TimetableLesson.id != lesson_id,
        )
    )
    if t_conflict.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Bu saatte öğretmenin başka dersi var (Öğretmen Çakışması).",
        )

    # Class conflict
    c_conflict = await db.execute(
        select(TimetableLesson).where(
            TimetableLesson.timetable_id == timetable_id,
            TimetableLesson.class_id == lesson.class_id,
            TimetableLesson.day == data.new_day,
            TimetableLesson.period == data.new_period,
            TimetableLesson.id != lesson_id,
        )
    )
    if c_conflict.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Bu saatte sınıfın başka dersi var (Sınıf Çakışması).",
        )

    # Update position
    lesson.day = data.new_day
    lesson.period = data.new_period
    await db.commit()
    await db.refresh(lesson)

    return TimetableLessonResponse.model_validate(lesson)


@router.get("/{timetable_id}/versions", response_model=list[TimetableVersionResponse])
async def list_timetable_versions(
    timetable_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    query = (
        select(TimetableVersion)
        .where(TimetableVersion.timetable_id == timetable_id)
        .order_by(TimetableVersion.version_number.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/{timetable_id}/versions/{version_id}/restore", response_model=TimetableResponse)
async def restore_timetable_version(
    timetable_id: int,
    version_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    v_result = await db.execute(
        select(TimetableVersion).where(
            TimetableVersion.id == version_id,
            TimetableVersion.timetable_id == timetable_id,
        )
    )
    version = v_result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Versiyon bulunamadı.")

    # Delete existing lessons
    from sqlalchemy import delete
    await db.execute(delete(TimetableLesson).where(TimetableLesson.timetable_id == timetable_id))

    # Restore from snapshot
    restored_lessons = [TimetableLesson(**item) for item in version.lessons_snapshot]
    db.add_all(restored_lessons)

    t_result = await db.execute(select(Timetable).where(Timetable.id == timetable_id))
    timetable = t_result.scalar_one()
    timetable.status = TimetableStatus.GENERATED
    await db.commit()
    await db.refresh(timetable)

    return timetable


@router.websocket("/ws/{timetable_id}")
async def solver_progress_websocket(websocket: WebSocket, timetable_id: int):
    await websocket.accept()
    redis = await get_redis()
    pubsub = redis.pubsub()
    channel = f"solver_progress_{timetable_id}"
    await pubsub.subscribe(channel)

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        await pubsub.unsubscribe(channel)
