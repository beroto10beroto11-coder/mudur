from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.models.class_ import ClassGroup
from app.repositories.class_ import ClassGroupRepository
from app.schemas.class_ import ClassGroupCreate, ClassGroupUpdate


class ClassGroupService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.class_repo = ClassGroupRepository(db)

    async def get_all_classes(self, school_id: int, skip: int = 0, limit: int = 100) -> list[ClassGroup]:
        return await self.class_repo.get_all(school_id=school_id, skip=skip, limit=limit)

    async def get_class(self, class_id: int) -> ClassGroup:
        cls = await self.class_repo.get_by_id(class_id)
        if not cls:
            raise NotFoundError("Sınıf bulunamadı.")
        return cls

    async def create_class(self, school_id: int, data: ClassGroupCreate) -> ClassGroup:
        data_dict = data.model_dump()
        data_dict["school_id"] = school_id
        return await self.class_repo.create(data_dict)

    async def update_class(self, class_id: int, data: ClassGroupUpdate) -> ClassGroup:
        cls = await self.get_class(class_id)
        return await self.class_repo.update(cls, data.model_dump(exclude_unset=True))

    async def delete_class(self, class_id: int) -> bool:
        return await self.class_repo.delete(class_id, soft=True)
