from sqlalchemy.ext.asyncio import AsyncSession
from app.models.classroom import Classroom
from app.repositories.base import BaseRepository


class ClassroomRepository(BaseRepository[Classroom]):
    def __init__(self, db: AsyncSession):
        super().__init__(Classroom, db)
