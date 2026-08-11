from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.timeslot import TimeSlot
from app.repositories.base import BaseRepository


class TimeSlotRepository(BaseRepository[TimeSlot]):
    def __init__(self, db: AsyncSession):
        super().__init__(TimeSlot, db)

    async def get_by_academic_year(self, academic_year_id: int) -> list[TimeSlot]:
        query = (
            select(TimeSlot)
            .where(TimeSlot.academic_year_id == academic_year_id, TimeSlot.is_active == True)
            .order_by(TimeSlot.day, TimeSlot.period)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
