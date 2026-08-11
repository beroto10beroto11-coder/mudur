from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.teacher import Teacher, TeacherAvailability
from app.repositories.base import BaseRepository


class TeacherRepository(BaseRepository[Teacher]):
    def __init__(self, db: AsyncSession):
        super().__init__(Teacher, db)


class TeacherAvailabilityRepository(BaseRepository[TeacherAvailability]):
    def __init__(self, db: AsyncSession):
        super().__init__(TeacherAvailability, db)

    async def get_by_teacher_and_year(self, teacher_id: int, academic_year_id: int) -> list[TeacherAvailability]:
        result = await self.db.execute(
            select(TeacherAvailability).where(
                TeacherAvailability.teacher_id == teacher_id,
                TeacherAvailability.academic_year_id == academic_year_id
            )
        )
        return list(result.scalars().all())
