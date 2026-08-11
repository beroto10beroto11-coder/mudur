import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.timetable import Timetable, TimetableLesson
from app.models.assignment import CourseAssignment
from app.models.class_ import ClassGroup
from app.models.classroom import Classroom
from app.models.teacher import Teacher, TeacherAvailability
from app.models.timeslot import TimeSlot
from app.solver.engine import TimetableSolver


async def main():
    async with AsyncSessionLocal() as session:
        school_id = 1
        academic_year_id = 1

        teachers_res = await session.execute(select(Teacher).where(Teacher.school_id == school_id, Teacher.is_active == True))
        teachers = list(teachers_res.scalars().all())

        classes_res = await session.execute(select(ClassGroup).where(ClassGroup.school_id == school_id, ClassGroup.is_active == True))
        classes = list(classes_res.scalars().all())

        rooms_res = await session.execute(select(Classroom).where(Classroom.school_id == school_id, Classroom.is_active == True))
        classrooms = list(rooms_res.scalars().all())

        asgns_res = await session.execute(select(CourseAssignment).where(CourseAssignment.school_id == school_id, CourseAssignment.academic_year_id == academic_year_id, CourseAssignment.is_active == True))
        assignments = list(asgns_res.scalars().all())

        slots_res = await session.execute(select(TimeSlot).where(TimeSlot.academic_year_id == academic_year_id, TimeSlot.is_active == True))
        timeslots = list(slots_res.scalars().all())

        avail_res = await session.execute(select(TeacherAvailability).where(TeacherAvailability.academic_year_id == academic_year_id))
        availabilities = list(avail_res.scalars().all())

        print(f"[DEBUG] Loaded {len(teachers)} teachers, {len(classes)} classes, {len(classrooms)} rooms, {len(assignments)} assignments, {len(timeslots)} timeslots")

        solver_engine = TimetableSolver(
            assignments=assignments,
            teachers=teachers,
            classes=classes,
            classrooms=classrooms,
            timeslots=timeslots,
            availabilities=availabilities,
            timetable_id=1,
        )

        t0 = time.time()
        result = solver_engine.solve(max_time_seconds=10)
        t1 = time.time()

        print(f"[DEBUG] Solve finished in {t1-t0:.2f}s")
        print(f"[DEBUG] Success: {result['success']}, Status: {result['status']}")
        print(f"[DEBUG] Generated Lessons: {len(result['lessons'])}")
        if result['conflicts']:
            print(f"[DEBUG] Conflicts: {result['conflicts']}")


if __name__ == "__main__":
    asyncio.run(main())
