from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.timetable import Timetable, TimetableLesson, TimetableVersion
from app.repositories.base import BaseRepository


class TimetableRepository(BaseRepository[Timetable]):
    def __init__(self, db: AsyncSession):
        super().__init__(Timetable, db)

    async def get_with_lessons(self, timetable_id: int) -> Timetable | None:
        query = (
            select(Timetable)
            .where(Timetable.id == timetable_id)
            .options(
                selectinload(Timetable.lessons).selectinload(TimetableLesson.course_assignment)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


class TimetableLessonRepository(BaseRepository[TimetableLesson]):
    def __init__(self, db: AsyncSession):
        super().__init__(TimetableLesson, db)

    async def get_by_timetable(self, timetable_id: int) -> list[TimetableLesson]:
        query = select(TimetableLesson).where(TimetableLesson.timetable_id == timetable_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())


class TimetableVersionRepository(BaseRepository[TimetableVersion]):
    def __init__(self, db: AsyncSession):
        super().__init__(TimetableVersion, db)

    async def get_by_timetable(self, timetable_id: int) -> list[TimetableVersion]:
        query = (
            select(TimetableVersion)
            .where(TimetableVersion.timetable_id == timetable_id)
            .order_by(TimetableVersion.version_number.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
