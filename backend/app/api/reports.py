from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.database import get_db
from app.models.teacher import Teacher
from app.models.class_ import ClassGroup
from app.models.course import Course
from app.models.classroom import Classroom
from app.models.timetable import Timetable, TimetableStatus

router = APIRouter(prefix="/reports", tags=["Reports & Dashboard"])


@router.get("/dashboard-stats")
async def get_dashboard_stats(
    school_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    teacher_count = (await db.execute(select(func.count()).where(Teacher.school_id == school_id, Teacher.is_active == True))).scalar_one()
    class_count = (await db.execute(select(func.count()).where(ClassGroup.school_id == school_id, ClassGroup.is_active == True))).scalar_one()
    course_count = (await db.execute(select(func.count()).where(Course.school_id == school_id, Course.is_active == True))).scalar_one()
    classroom_count = (await db.execute(select(func.count()).where(Classroom.school_id == school_id, Classroom.is_active == True))).scalar_one()

    latest_timetable = (
        await db.execute(
            select(Timetable)
            .where(Timetable.school_id == school_id)
            .order_by(Timetable.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    return {
        "total_teachers": teacher_count,
        "total_classes": class_count,
        "total_courses": course_count,
        "total_classrooms": classroom_count,
        "latest_timetable_name": latest_timetable.name if latest_timetable else None,
        "latest_timetable_status": latest_timetable.status.value if latest_timetable else None,
        "open_conflicts_count": len(latest_timetable.solver_conflicts.get("conflicts", [])) if (latest_timetable and latest_timetable.solver_conflicts) else 0,
    }
