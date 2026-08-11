from sqlalchemy.ext.asyncio import AsyncSession
from app.models.class_ import ClassGroup
from app.repositories.base import BaseRepository


class ClassGroupRepository(BaseRepository[ClassGroup]):
    def __init__(self, db: AsyncSession):
        super().__init__(ClassGroup, db)
