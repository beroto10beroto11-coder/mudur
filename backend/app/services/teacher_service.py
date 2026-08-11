from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.models.teacher import Teacher, TeacherAvailability
from app.repositories.teacher import TeacherRepository, TeacherAvailabilityRepository
from app.schemas.teacher import TeacherCreate, TeacherUpdate
from app.schemas.availability import TeacherAvailabilityBatchUpdate


class TeacherService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.teacher_repo = TeacherRepository(db)
        self.avail_repo = TeacherAvailabilityRepository(db)

    async def get_all_teachers(self, school_id: int, skip: int = 0, limit: int = 100) -> list[Teacher]:
        return await self.teacher_repo.get_all(school_id=school_id, skip=skip, limit=limit)

    async def get_teacher(self, teacher_id: int) -> Teacher:
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise NotFoundError("Öğretmen bulunamadı.")
        return teacher

    async def create_teacher(self, school_id: int, data: TeacherCreate) -> Teacher:
        data_dict = data.model_dump()
        data_dict["school_id"] = school_id
        return await self.teacher_repo.create(data_dict)

    async def update_teacher(self, teacher_id: int, data: TeacherUpdate) -> Teacher:
        teacher = await self.get_teacher(teacher_id)
        return await self.teacher_repo.update(teacher, data.model_dump(exclude_unset=True))

    async def delete_teacher(self, teacher_id: int) -> bool:
        return await self.teacher_repo.delete(teacher_id, soft=True)

    # Availability methods
    async def get_availability(self, teacher_id: int, academic_year_id: int) -> list[TeacherAvailability]:
        return await self.avail_repo.get_by_teacher_and_year(teacher_id, academic_year_id)

    async def update_availability(self, data: TeacherAvailabilityBatchUpdate) -> bool:
        # Clear existing unavailabilities for teacher/year
        existing = await self.avail_repo.get_by_teacher_and_year(data.teacher_id, data.academic_year_id)
        for item in existing:
            await self.db.delete(item)

        # Add new availability records
        for item in data.unavailabilities:
            avail_obj = TeacherAvailability(
                teacher_id=data.teacher_id,
                academic_year_id=data.academic_year_id,
                day=item["day"],
                period=item["period"],
                available=item.get("available", False),
                preference=item.get("preference", 0),
                reason=item.get("reason"),
            )
            self.db.add(avail_obj)
        await self.db.commit()
        return True
