from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.models.classroom import Classroom
from app.repositories.classroom import ClassroomRepository
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate


class ClassroomService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.classroom_repo = ClassroomRepository(db)

    async def get_all_classrooms(self, school_id: int, skip: int = 0, limit: int = 100) -> list[Classroom]:
        return await self.classroom_repo.get_all(school_id=school_id, skip=skip, limit=limit)

    async def get_classroom(self, classroom_id: int) -> Classroom:
        room = await self.classroom_repo.get_by_id(classroom_id)
        if not room:
            raise NotFoundError("Derslik bulunamadı.")
        return room

    async def create_classroom(self, school_id: int, data: ClassroomCreate) -> Classroom:
        data_dict = data.model_dump()
        data_dict["school_id"] = school_id
        return await self.classroom_repo.create(data_dict)

    async def update_classroom(self, classroom_id: int, data: ClassroomUpdate) -> Classroom:
        room = await self.get_classroom(classroom_id)
        return await self.classroom_repo.update(room, data.model_dump(exclude_unset=True))

    async def delete_classroom(self, classroom_id: int) -> bool:
        return await self.classroom_repo.delete(classroom_id, soft=True)
