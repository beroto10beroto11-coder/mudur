from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.school import School, AcademicYear
from app.repositories.base import BaseRepository


class SchoolRepository(BaseRepository[School]):
    def __init__(self, db: AsyncSession):
        super().__init__(School, db)


class AcademicYearRepository(BaseRepository[AcademicYear]):
    def __init__(self, db: AsyncSession):
        super().__init__(AcademicYear, db)

    async def get_active_year(self, school_id: int) -> AcademicYear | None:
        result = await self.db.execute(
            select(AcademicYear).where(
                AcademicYear.school_id == school_id,
                AcademicYear.is_active == True
            )
        )
        return result.scalar_one_or_none()
