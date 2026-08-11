"""Initial migration: create all tables

Revision ID: 001_initial
Revises:
Create Date: 2026-08-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enums ──────────────────────────────────────────────────────────────
    user_role_enum = postgresql.ENUM(
        "SUPER_ADMIN", "SCHOOL_ADMIN", "VICE_PRINCIPAL", "TEACHER", "VIEWER",
        name="user_role_enum",
    )
    user_role_enum.create(op.get_bind(), checkfirst=True)

    timetable_status_enum = postgresql.ENUM(
        "DRAFT", "GENERATING", "GENERATED", "PUBLISHED", "ARCHIVED", "FAILED",
        name="timetable_status_enum",
    )
    timetable_status_enum.create(op.get_bind(), checkfirst=True)

    backup_status_enum = postgresql.ENUM(
        "PENDING", "RUNNING", "SUCCESS", "FAILED",
        name="backup_status_enum",
    )
    backup_status_enum.create(op.get_bind(), checkfirst=True)

    backup_type_enum = postgresql.ENUM(
        "MANUAL", "AUTOMATIC",
        name="backup_type_enum",
    )
    backup_type_enum.create(op.get_bind(), checkfirst=True)

    # ── schools ────────────────────────────────────────────────────────────
    op.create_table(
        "schools",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("short_name", sa.String(50), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_schools_name", "schools", ["name"])

    # ── academic_years ─────────────────────────────────────────────────────
    op.create_table(
        "academic_years",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(20), nullable=False),
        sa.Column("start_date", sa.String(10), nullable=True),
        sa.Column("end_date", sa.String(10), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("days_per_week", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("periods_per_day", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("school_id", "name", name="uq_academic_year_school_name"),
    )
    op.create_index("ix_academic_years_school_id", "academic_years", ["school_id"])
    op.create_index("ix_academic_years_active", "academic_years", ["school_id", "is_active"])

    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("hashed_password", sa.String(500), nullable=False),
        sa.Column("global_role", sa.Enum("SUPER_ADMIN", "SCHOOL_ADMIN", "VICE_PRINCIPAL", "TEACHER", "VIEWER", name="user_role_enum"), nullable=False, server_default="VIEWER"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("teacher_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_global_role", "users", ["global_role"])

    # ── refresh_tokens ─────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(500), nullable=False, unique=True),
        sa.Column("expires_at", sa.String(50), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    # ── user_schools ───────────────────────────────────────────────────────
    op.create_table(
        "user_schools",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role", sa.Enum("SUPER_ADMIN", "SCHOOL_ADMIN", "VICE_PRINCIPAL", "TEACHER", "VIEWER", name="user_role_enum"), nullable=False, server_default="VIEWER"),
    )

    # ── teachers ───────────────────────────────────────────────────────────
    op.create_table(
        "teachers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("branch", sa.String(100), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("max_daily_hours", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("max_weekly_hours", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_teachers_school_id", "teachers", ["school_id"])
    op.create_index("ix_teachers_branch", "teachers", ["branch"])
    op.create_index("ix_teachers_active", "teachers", ["school_id", "is_active"])

    # ── teacher_availability ───────────────────────────────────────────────
    op.create_table(
        "teacher_availability",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_year_id", sa.Integer(), sa.ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("preference", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reason", sa.String(200), nullable=True),
        sa.UniqueConstraint("teacher_id", "academic_year_id", "day", "period", name="uq_teacher_availability"),
    )
    op.create_index("ix_teacher_avail_teacher", "teacher_availability", ["teacher_id", "academic_year_id"])

    # ── courses ────────────────────────────────────────────────────────────
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("code", sa.String(20), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("branch", sa.String(100), nullable=True),
        sa.Column("weekly_hours", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("consecutive_hours", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("requires_classroom", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("required_room_type", sa.String(50), nullable=True),
        sa.Column("is_elective", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("school_id", "name", name="uq_course_school_name"),
    )
    op.create_index("ix_courses_school_id", "courses", ["school_id"])
    op.create_index("ix_courses_branch", "courses", ["branch"])

    # ── classes ────────────────────────────────────────────────────────────
    op.create_table(
        "classes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("grade", sa.Integer(), nullable=False),
        sa.Column("section", sa.String(10), nullable=False),
        sa.Column("student_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("max_daily_hours", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("school_id", "grade", "section", name="uq_class_school_grade_section"),
    )
    op.create_index("ix_classes_school_id", "classes", ["school_id"])
    op.create_index("ix_classes_grade", "classes", ["school_id", "grade"])

    # ── classrooms ─────────────────────────────────────────────────────────
    op.create_table(
        "classrooms",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("room_type", sa.String(50), nullable=False, server_default="normal"),
        sa.Column("floor", sa.Integer(), nullable=True),
        sa.Column("building", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("school_id", "name", name="uq_classroom_school_name"),
    )
    op.create_index("ix_classrooms_school_id", "classrooms", ["school_id"])
    op.create_index("ix_classrooms_room_type", "classrooms", ["school_id", "room_type"])

    # ── course_assignments ─────────────────────────────────────────────────
    op.create_table(
        "course_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_year_id", sa.Integer(), sa.ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("classroom_id", sa.Integer(), sa.ForeignKey("classrooms.id", ondelete="SET NULL"), nullable=True),
        sa.Column("weekly_hours", sa.Integer(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("is_fixed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("fixed_day", sa.Integer(), nullable=True),
        sa.Column("fixed_period", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("academic_year_id", "course_id", "teacher_id", "class_id", name="uq_course_assignment"),
    )
    op.create_index("ix_course_assignments_school", "course_assignments", ["school_id", "academic_year_id"])
    op.create_index("ix_course_assignments_teacher", "course_assignments", ["teacher_id", "academic_year_id"])
    op.create_index("ix_course_assignments_class", "course_assignments", ["class_id", "academic_year_id"])

    # ── time_slots ─────────────────────────────────────────────────────────
    op.create_table(
        "time_slots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_year_id", sa.Integer(), sa.ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.String(5), nullable=False),
        sa.Column("end_time", sa.String(5), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.UniqueConstraint("academic_year_id", "day", "period", name="uq_timeslot_academic_year_day_period"),
    )
    op.create_index("ix_time_slots_academic_year", "time_slots", ["academic_year_id"])
    op.create_index("ix_time_slots_day_period", "time_slots", ["academic_year_id", "day", "period"])

    # ── timetables ─────────────────────────────────────────────────────────
    op.create_table(
        "timetables",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_year_id", sa.Integer(), sa.ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("DRAFT", "GENERATING", "GENERATED", "PUBLISHED", "ARCHIVED", "FAILED", name="timetable_status_enum"), nullable=False, server_default="DRAFT"),
        sa.Column("solver_job_id", sa.String(100), nullable=True),
        sa.Column("solver_duration_seconds", sa.Float(), nullable=True),
        sa.Column("solver_objective_value", sa.Float(), nullable=True),
        sa.Column("solver_conflicts", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_timetables_school", "timetables", ["school_id", "academic_year_id"])
    op.create_index("ix_timetables_status", "timetables", ["status"])

    # ── timetable_lessons ──────────────────────────────────────────────────
    op.create_table(
        "timetable_lessons",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("timetable_id", sa.Integer(), sa.ForeignKey("timetables.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_assignment_id", sa.Integer(), sa.ForeignKey("course_assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("classroom_id", sa.Integer(), nullable=True),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("is_fixed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("timetable_id", "teacher_id", "day", "period", name="uq_lesson_teacher_slot"),
        sa.UniqueConstraint("timetable_id", "class_id", "day", "period", name="uq_lesson_class_slot"),
    )
    op.create_index("ix_timetable_lessons_timetable", "timetable_lessons", ["timetable_id"])
    op.create_index("ix_timetable_lessons_teacher", "timetable_lessons", ["timetable_id", "teacher_id"])
    op.create_index("ix_timetable_lessons_class", "timetable_lessons", ["timetable_id", "class_id"])
    op.create_index("ix_timetable_lessons_day_period", "timetable_lessons", ["timetable_id", "day", "period"])

    # ── timetable_versions ─────────────────────────────────────────────────
    op.create_table(
        "timetable_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("timetable_id", sa.Integer(), sa.ForeignKey("timetables.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(200), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("lessons_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("timetable_id", "version_number", name="uq_timetable_version"),
    )
    op.create_index("ix_timetable_versions_timetable", "timetable_versions", ["timetable_id"])

    # ── duties ─────────────────────────────────────────────────────────────
    op.create_table(
        "duties",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_year_id", sa.Integer(), sa.ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("shift", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("location", sa.String(150), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("automatic", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("week_number", sa.Integer(), nullable=True),
        sa.Column("duty_date", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_duties_school", "duties", ["school_id", "academic_year_id"])
    op.create_index("ix_duties_teacher", "duties", ["teacher_id"])
    op.create_index("ix_duties_day", "duties", ["academic_year_id", "day"])

    # ── students ───────────────────────────────────────────────────────────
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_year_id", sa.Integer(), sa.ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_number", sa.String(30), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_students_school", "students", ["school_id", "academic_year_id"])
    op.create_index("ix_students_class", "students", ["class_id"])

    # ── elective_courses ───────────────────────────────────────────────────
    op.create_table(
        "elective_courses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_year_id", sa.Integer(), sa.ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("min_students", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("max_students", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("eligible_grades", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_elective_courses_school", "elective_courses", ["school_id", "academic_year_id"])

    # ── elective_groups ────────────────────────────────────────────────────
    op.create_table(
        "elective_groups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("elective_course_id", sa.Integer(), sa.ForeignKey("elective_courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("classroom_id", sa.Integer(), sa.ForeignKey("classrooms.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("day", sa.Integer(), nullable=True),
        sa.Column("period", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_elective_groups_course", "elective_groups", ["elective_course_id"])

    # ── student_choices ────────────────────────────────────────────────────
    op.create_table(
        "student_choices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("elective_course_id", sa.Integer(), sa.ForeignKey("elective_courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("elective_group_id", sa.Integer(), sa.ForeignKey("elective_groups.id", ondelete="SET NULL"), nullable=True),
        sa.Column("preference_rank", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_assigned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("student_id", "elective_course_id", name="uq_student_choice"),
    )
    op.create_index("ix_student_choices_student", "student_choices", ["student_id"])

    # ── audit_logs ─────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("school_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("entity_name", sa.String(200), nullable=True),
        sa.Column("old_data", sa.JSON(), nullable=True),
        sa.Column("new_data", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_user", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_school", "audit_logs", ["school_id"])
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    # ── backups ────────────────────────────────────────────────────────────
    op.create_table(
        "backups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("status", sa.Enum("PENDING", "RUNNING", "SUCCESS", "FAILED", name="backup_status_enum"), nullable=False, server_default="PENDING"),
        sa.Column("backup_type", sa.Enum("MANUAL", "AUTOMATIC", name="backup_type_enum"), nullable=False, server_default="MANUAL"),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_backups_status", "backups", ["status"])
    op.create_index("ix_backups_type", "backups", ["backup_type"])
    op.create_index("ix_backups_created_at", "backups", ["created_at"])

    # ── announcements ──────────────────────────────────────────────────────
    op.create_table(
        "announcements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("expires_at", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_announcements_school", "announcements", ["school_id"])
    op.create_index("ix_announcements_pinned", "announcements", ["school_id", "is_pinned"])

    # ── system_settings ────────────────────────────────────────────────────
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=True),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("description", sa.String(300), nullable=True),
        sa.Column("value_type", sa.String(20), nullable=False, server_default="string"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("school_id", "key", name="uq_system_setting_school_key"),
    )
    op.create_index("ix_system_settings_school", "system_settings", ["school_id"])
    op.create_index("ix_system_settings_key", "system_settings", ["key"])

    # ── Add FK from users.teacher_id → teachers.id ─────────────────────────
    op.create_foreign_key(
        "fk_users_teacher_id",
        "users", "teachers",
        ["teacher_id"], ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Drop FK first
    op.drop_constraint("fk_users_teacher_id", "users", type_="foreignkey")

    # Drop tables in reverse dependency order
    for table in [
        "system_settings",
        "announcements",
        "backups",
        "audit_logs",
        "student_choices",
        "elective_groups",
        "elective_courses",
        "students",
        "duties",
        "timetable_versions",
        "timetable_lessons",
        "timetables",
        "time_slots",
        "course_assignments",
        "classrooms",
        "classes",
        "courses",
        "teacher_availability",
        "teachers",
        "user_schools",
        "refresh_tokens",
        "users",
        "academic_years",
        "schools",
    ]:
        op.drop_table(table)

    # Drop enums
    for enum_name in ["user_role_enum", "timetable_status_enum", "backup_status_enum", "backup_type_enum"]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
