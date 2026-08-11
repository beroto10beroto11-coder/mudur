"""
Celery task for async OR-Tools Timetable solving with Redis progress reporting.
"""
import asyncio
import json

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.core.redis import publish_progress
from app.models.course import Course
from app.models.assignment import CourseAssignment
from app.models.class_ import ClassGroup
from app.models.classroom import Classroom
from app.models.teacher import Teacher, TeacherAvailability
from app.models.timeslot import TimeSlot
from app.models.timetable import Timetable, TimetableLesson, TimetableStatus, TimetableVersion
from app.solver.engine import TimetableSolver
from app.worker import celery_app


async def _execute_solver(timetable_id: int, school_id: int, academic_year_id: int):
    async with AsyncSessionLocal() as session:
        # Load timetable
        result = await session.execute(select(Timetable).where(Timetable.id == timetable_id))
        timetable = result.scalar_one_or_none()
        if not timetable:
            return

        timetable.status = TimetableStatus.GENERATING
        await session.commit()

        # Load all required data for solver
        teachers_res = await session.execute(select(Teacher).where(Teacher.school_id == school_id, Teacher.is_active == True))
        teachers = list(teachers_res.scalars().all())

        classes_res = await session.execute(select(ClassGroup).where(ClassGroup.school_id == school_id, ClassGroup.is_active == True))
        classes = list(classes_res.scalars().all())

        rooms_res = await session.execute(select(Classroom).where(Classroom.school_id == school_id, Classroom.is_active == True))
        classrooms = list(rooms_res.scalars().all())

        asgns_res = await session.execute(
            select(CourseAssignment)
            .options(selectinload(CourseAssignment.course))
            .where(
                CourseAssignment.school_id == school_id,
                CourseAssignment.academic_year_id == academic_year_id,
                CourseAssignment.is_active == True,
            )
        )
        assignments = list(asgns_res.scalars().all())

        # If no explicit CourseAssignments exist, dynamically synthesize them from Courses, Classes, and Teacher competencies
        if not assignments:
            courses_res = await session.execute(
                select(Course).where(Course.school_id == school_id, Course.is_active == True)
            )
            courses = list(courses_res.scalars().all())

            synthesized_asgns = []
            asgn_id_counter = 1000

            for cls in classes:
                for crs in courses:
                    # Check if course applies to class
                    c_target = crs.target_classes or "ALL"
                    if c_target != "ALL" and cls.name not in [x.strip() for x in c_target.split(",")]:
                        continue

                    # Find candidate teachers who can teach this course to this class
                    candidate_teachers = []
                    for t in teachers:
                        t_c = t.allowed_courses or "ALL"
                        t_cl = t.allowed_classes or "ALL"

                        can_teach_course = (t_c == "ALL") or (crs.name in [x.strip() for x in t_c.split(",")]) or (t.branch and crs.branch and t.branch.lower() == crs.branch.lower())
                        can_teach_class = (t_cl == "ALL") or (cls.name in [x.strip() for x in t_cl.split(",")])

                        if can_teach_course and can_teach_class:
                            candidate_teachers.append(t)

                    if not candidate_teachers:
                        candidate_teachers = teachers  # Fallback

                    chosen_t = candidate_teachers[0]

                    mock_asgn = CourseAssignment(
                        id=asgn_id_counter,
                        school_id=school_id,
                        academic_year_id=academic_year_id,
                        course_id=crs.id,
                        teacher_id=chosen_t.id,
                        class_id=cls.id,
                        weekly_hours=crs.weekly_hours,
                        consecutive_hours=crs.consecutive_hours,
                        is_fixed=False,
                    )
                    mock_asgn.course = crs
                    synthesized_asgns.append(mock_asgn)
                    asgn_id_counter += 1

            assignments = synthesized_asgns

        slots_res = await session.execute(
            select(TimeSlot).where(TimeSlot.academic_year_id == academic_year_id, TimeSlot.is_active == True)
        )
        timeslots = list(slots_res.scalars().all())

        avail_res = await session.execute(
            select(TeacherAvailability).where(TeacherAvailability.academic_year_id == academic_year_id)
        )
        availabilities = list(avail_res.scalars().all())

        # Define progress callback for WebSocket / Redis channel
        channel_name = f"solver_progress_{timetable_id}"
        loop = asyncio.get_running_loop()

        def progress_cb(data: dict):
            try:
                asyncio.run_coroutine_threadsafe(publish_progress(channel_name, json.dumps(data)), loop)
            except Exception:
                pass

        # Create & run solver
        solver_engine = TimetableSolver(
            assignments=assignments,
            teachers=teachers,
            classes=classes,
            classrooms=classrooms,
            timeslots=timeslots,
            availabilities=availabilities,
            timetable_id=timetable_id,
        )

        solver_result = solver_engine.solve(max_time_seconds=30, progress_callback=progress_cb)

        if solver_result["success"]:
            # Delete old lessons if any
            from sqlalchemy import delete
            await session.execute(delete(TimetableLesson).where(TimetableLesson.timetable_id == timetable_id))

            # Save new lessons
            new_lessons = [TimetableLesson(**item) for item in solver_result["lessons"]]
            session.add_all(new_lessons)

            timetable.status = TimetableStatus.GENERATED
            timetable.solver_duration_seconds = solver_result["duration_seconds"]
            timetable.solver_objective_value = solver_result["objective_value"]
            timetable.solver_conflicts = None

            # Create Version 1 snapshot
            version_snapshot = TimetableVersion(
                timetable_id=timetable_id,
                version_number=1,
                description="Otomatik solver üretimi",
                change_summary=f"{len(new_lessons)} ders başarıyla yerleştirildi.",
                lessons_snapshot=solver_result["lessons"],
            )
            session.add(version_snapshot)
        else:
            timetable.status = TimetableStatus.FAILED
            timetable.solver_duration_seconds = solver_result["duration_seconds"]
            timetable.solver_conflicts = {"conflicts": solver_result["conflicts"]}

        await session.commit()
        await publish_progress(
            channel_name,
            json.dumps({
                "percent": 100,
                "status": timetable.status.value,
                "success": solver_result["success"],
            }),
        )


@celery_app.task(name="app.tasks.solver_task.run_solver")
def run_solver(timetable_id: int, school_id: int, academic_year_id: int):
    asyncio.run(_execute_solver(timetable_id, school_id, academic_year_id))
