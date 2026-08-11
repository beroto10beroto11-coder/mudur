from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.assignment import CourseAssignment
from app.repositories.base import BaseRepository


class CourseAssignmentRepository(BaseRepository[CourseAssignment]):
    def __init__(self, db: AsyncSession):
        super().__init__(CourseAssignment, db)

    async def get_all_with_relations(self, school_id: int, academic_year_id: int) -> list[CourseAssignment]:
        query = (
            select(CourseAssignment)
            .where(
                CourseAssignment.school_id == school_id,
                CourseAssignment.academic_year_id == academic_year_id,
                CourseAssignment.is_active == True,
            )
            .options(
                selectinload(CourseAssignment.course),
                selectinload(CourseAssignment.teacher),
                selectinload(CourseAssignment.class_group),
                selectinload(CourseAssignment.classroom),
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
