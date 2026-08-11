"""
Development database seed script.
Populates initial sample school, academic year, teachers, classes, courses, classrooms, assignments, and time slots.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.auth.password import hash_password
from app.models.user import User, UserRole, user_school_association
from app.models.school import School, AcademicYear
from app.models.teacher import Teacher
from app.models.course import Course
from app.models.class_ import ClassGroup
from app.models.classroom import Classroom
from app.models.assignment import CourseAssignment
from app.models.timeslot import TimeSlot


async def seed_data():
    from app.core.database import engine, Base
    import app.models  # noqa: F401
    try:
        from scripts.migrate_sqlite import apply_sqlite_migrations
        db_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "school_scheduler.db")
        apply_sqlite_migrations(db_file)
    except Exception as e:
        pass

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        print("[+] Starting database seed...")

        # 1. Superadmin User
        superadmin = (await session.execute(select(User).where(User.email == "admin@school.k12.tr"))).scalar_one_or_none()
        if not superadmin:
            superadmin = User(
                email="admin@school.k12.tr",
                full_name="System Administrator",
                hashed_password=hash_password("admin123456"),
                global_role=UserRole.SUPER_ADMIN,
                is_active=True,
                is_verified=True,
            )
            session.add(superadmin)
            await session.commit()
            await session.refresh(superadmin)
            print("  [OK] Created Superadmin user (admin@school.k12.tr / admin123456)")

        # 2. Sample School
        school = (await session.execute(select(School).where(School.name == "Atatürk Anadolu Lisesi"))).scalar_one_or_none()
        if not school:
            school = School(
                name="Atatürk Anadolu Lisesi",
                short_name="AAL",
                city="İstanbul",
                district="Kadıköy",
                email="info@aal.k12.tr",
                phone="0216 123 45 67",
                is_active=True,
            )
            session.add(school)
            await session.commit()
            await session.refresh(school)

            # Associate superadmin to school
            await session.execute(
                user_school_association.insert().values(
                    user_id=superadmin.id,
                    school_id=school.id,
                    role=UserRole.SCHOOL_ADMIN,
                )
            )
            await session.commit()
            print("  [OK] Created sample school: Atatürk Anadolu Lisesi")

        # 3. Academic Year
        year = (await session.execute(select(AcademicYear).where(AcademicYear.school_id == school.id, AcademicYear.name == "2026-2027"))).scalar_one_or_none()
        if not year:
            year = AcademicYear(
                school_id=school.id,
                name="2026-2027",
                start_date="2026-09-07",
                end_date="2027-06-18",
                is_active=True,
                days_per_week=5,
                periods_per_day=8,
            )
            session.add(year)
            await session.commit()
            await session.refresh(year)
            print("  [OK] Created Academic Year: 2026-2027")

        # 4. TimeSlots
        existing_slots = (await session.execute(select(TimeSlot).where(TimeSlot.academic_year_id == year.id))).scalars().all()
        if not existing_slots:
            period_times = [
                ("08:30", "09:10"), ("09:20", "10:00"), ("10:10", "10:50"), ("11:00", "11:40"),
                ("12:30", "13:10"), ("13:20", "14:00"), ("14:10", "14:50"), ("15:00", "15:40"),
            ]
            for day in range(5):
                for p_idx, (st, et) in enumerate(period_times, start=1):
                    slot = TimeSlot(
                        school_id=school.id,
                        academic_year_id=year.id,
                        day=day,
                        period=p_idx,
                        start_time=st,
                        end_time=et,
                        is_active=True,
                    )
                    session.add(slot)
            await session.commit()
            print("  [OK] Created 40 TimeSlots (5 days x 8 periods)")

        # 5. Classrooms
        rooms_data = [
            ("101 Nolu Derslik", 34, "normal"),
            ("102 Nolu Derslik", 34, "normal"),
            ("103 Nolu Derslik", 34, "normal"),
            ("Bilişim Laboratuvarı", 30, "lab_computer"),
            ("Fen Laboratuvarı", 30, "lab_science"),
        ]
        classrooms = []
        for name, cap, rtype in rooms_data:
            rm = (await session.execute(select(Classroom).where(Classroom.school_id == school.id, Classroom.name == name))).scalar_one_or_none()
            if not rm:
                rm = Classroom(school_id=school.id, name=name, capacity=cap, room_type=rtype)
                session.add(rm)
                await session.commit()
                await session.refresh(rm)
            classrooms.append(rm)
        print(f"  [OK] Ensured {len(classrooms)} Classrooms exist")

        # 6. Teachers
        teachers_data = [
            ("Ahmet", "Yılmaz", "Matematik"),
            ("Mehmet", "Kaya", "Fizik"),
            ("Ayşe", "Demir", "Kimya"),
            ("Fatma", "Şahin", "Biyoloji"),
            ("Zeynep", "Çelik", "Türk Dili ve Edebiyatı"),
            ("Ali", "Öztürk", "Tarih"),
            ("Mustafa", "Aydın", "Coğrafya"),
            ("Elif", "Yıldız", "İngilizce"),
            ("Emre", "Arslan", "Bilişim Teknolojileri"),
            ("Burak", "Kılıç", "Beden Eğitimi"),
        ]
        teachers = []
        for fn, ln, br in teachers_data:
            t = (await session.execute(select(Teacher).where(Teacher.school_id == school.id, Teacher.first_name == fn, Teacher.last_name == ln))).scalar_one_or_none()
            if not t:
                t = Teacher(school_id=school.id, first_name=fn, last_name=ln, branch=br, allowed_courses=br, allowed_classes="ALL")
                session.add(t)
                await session.commit()
                await session.refresh(t)
            teachers.append(t)
        print(f"  [OK] Ensured {len(teachers)} Teachers exist")

        # 7. Classes
        classes_data = [
            ("9/A", 9, "A", 32), ("9/B", 9, "B", 32),
            ("10/A", 10, "A", 30), ("10/B", 10, "B", 30),
            ("11/A", 11, "A", 28), ("11/B", 11, "B", 28),
            ("12/A", 12, "A", 25), ("12/B", 12, "B", 25),
        ]
        classes = []
        for name, grade, sec, cnt in classes_data:
            c = (await session.execute(select(ClassGroup).where(ClassGroup.school_id == school.id, ClassGroup.name == name))).scalar_one_or_none()
            if not c:
                c = ClassGroup(school_id=school.id, name=name, grade=grade, section=sec, student_count=cnt)
                session.add(c)
                await session.commit()
                await session.refresh(c)
            classes.append(c)
        print(f"  [OK] Ensured {len(classes)} ClassGroups exist")

        # 8. Courses
        courses_data = [
            ("Matematik", "MAT", "Matematik", 6, "2+2+1+1", False),
            ("Fizik", "FİZ", "Fizik", 4, "2+2", False),
            ("Kimya", "KİM", "Kimya", 4, "2+2", False),
            ("Biyoloji", "BİY", "Biyoloji", 4, "2+2", False),
            ("Türk Dili ve Edebiyatı", "TDE", "Türk Dili ve Edebiyatı", 5, "2+2+1", False),
            ("Tarih", "TAR", "Tarih", 2, "2", False),
            ("Coğrafya", "COĞ", "Coğrafya", 2, "2", False),
            ("İngilizce", "İNG", "İngilizce", 4, "2+2", False),
            ("Bilişim Teknolojileri", "BİL", "Bilişim Teknolojileri", 2, "2", True),
            ("Beden Eğitimi", "BED", "Beden Eğitimi", 2, "2", False),
        ]
        courses = []
        for cname, code, br, wh, dist, req_rm in courses_data:
            crs = (await session.execute(select(Course).where(Course.school_id == school.id, Course.name == cname))).scalar_one_or_none()
            if not crs:
                crs = Course(school_id=school.id, name=cname, code=code, branch=br, weekly_hours=wh, hour_distribution=dist, requires_classroom=req_rm)
                session.add(crs)
                await session.commit()
                await session.refresh(crs)
            else:
                crs.hour_distribution = dist
                await session.commit()
            courses.append(crs)
        print(f"  [OK] Ensured {len(courses)} Courses exist")

        # 9. Course Assignments
        existing_asgns = (await session.execute(select(CourseAssignment).where(CourseAssignment.academic_year_id == year.id))).scalars().all()
        if not existing_asgns:
            # Map teachers to courses by branch
            t_by_branch = {t.branch: t for t in teachers}

            for cls in classes[:4]:  # Assign to 9/A, 9/B, 10/A, 10/B
                for crs in courses:
                    teacher = t_by_branch.get(crs.branch, teachers[0])
                    room = classrooms[3] if crs.requires_classroom else None

                    asgn = CourseAssignment(
                        school_id=school.id,
                        academic_year_id=year.id,
                        course_id=crs.id,
                        teacher_id=teacher.id,
                        class_id=cls.id,
                        classroom_id=room.id if room else None,
                        weekly_hours=crs.weekly_hours,
                    )
                    session.add(asgn)
            await session.commit()
            print("  [OK] Created CourseAssignments for demo classes")

        print("[DONE] Database seed completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_data())
