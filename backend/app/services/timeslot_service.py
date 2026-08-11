from datetime import datetime, timedelta
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.timeslot import TimeSlot
from app.repositories.timeslot import TimeSlotRepository
from app.schemas.timeslot import TimeSlotBatchCreate, TimeSlotCreate


class TimeSlotService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.slot_repo = TimeSlotRepository(db)

    async def get_by_academic_year(self, academic_year_id: int) -> list[TimeSlot]:
        return await self.slot_repo.get_by_academic_year(academic_year_id)

    async def generate_default_slots(self, school_id: int, data: TimeSlotBatchCreate) -> list[TimeSlot]:
        # Clear existing slots for this academic year
        await self.db.execute(
            delete(TimeSlot).where(TimeSlot.academic_year_id == data.academic_year_id)
        )

        base_time = datetime.strptime(data.start_time_str, "%H:%M")
        created_slots: list[TimeSlot] = []

        for d in range(data.days):
            current_time = base_time
            for p in range(1, data.periods_per_day + 1):
                end_time = current_time + timedelta(minutes=data.lesson_duration_minutes)
                slot = TimeSlot(
                    school_id=school_id,
                    academic_year_id=data.academic_year_id,
                    day=d,
                    period=p,
                    start_time=current_time.strftime("%H:%M"),
                    end_time=end_time.strftime("%H:%M"),
                    is_active=True,
                )
                self.db.add(slot)
                created_slots.append(slot)
                current_time = end_time + timedelta(minutes=data.break_duration_minutes)

        await self.db.commit()
        return created_slots
