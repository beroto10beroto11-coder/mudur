"""Add allowed_courses, allowed_classes to teachers and target_classes to courses

Revision ID: 002_add_teacher_course_fields
Revises: 001_initial
Create Date: 2026-08-11

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "002_add_teacher_course_fields"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add allowed_courses & allowed_classes to teachers table
    op.add_column("teachers", sa.Column("allowed_courses", sa.String(length=500), nullable=True, server_default="ALL"))
    op.add_column("teachers", sa.Column("allowed_classes", sa.String(length=500), nullable=True, server_default="ALL"))

    # Add target_classes to courses table
    op.add_column("courses", sa.Column("target_classes", sa.String(length=255), nullable=True, server_default="ALL"))


def downgrade() -> None:
    op.drop_column("teachers", "allowed_classes")
    op.drop_column("teachers", "allowed_courses")
    op.drop_column("courses", "target_classes")
