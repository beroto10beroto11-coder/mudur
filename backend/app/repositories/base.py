from typing import Generic, TypeVar, Any
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: int) -> ModelType | None:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        school_id: int | None = None,
        include_inactive: bool = False,
    ) -> list[ModelType]:
        query = select(self.model)
        if school_id is not None and hasattr(self.model, "school_id"):
            query = query.where(getattr(self.model, "school_id") == school_id)
        if not include_inactive and hasattr(self.model, "is_active"):
            query = query.where(getattr(self.model, "is_active") == True)
        if hasattr(self.model, "is_deleted"):
            query = query.where(getattr(self.model, "is_deleted") == False)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self, school_id: int | None = None) -> int:
        query = select(func.count()).select_from(self.model)
        if school_id is not None and hasattr(self.model, "school_id"):
            query = query.where(getattr(self.model, "school_id") == school_id)
        if hasattr(self.model, "is_deleted"):
            query = query.where(getattr(self.model, "is_deleted") == False)

        result = await self.db.execute(query)
        return result.scalar_one() or 0

    async def create(self, obj_in: dict[str, Any] | ModelType) -> ModelType:
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        else:
            db_obj = obj_in
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: dict[str, Any]) -> ModelType:
        for field, value in obj_in.items():
            if value is not None and hasattr(db_obj, field):
                setattr(db_obj, field, value)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: int, soft: bool = True) -> bool:
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return False
        if soft and hasattr(db_obj, "soft_delete"):
            db_obj.soft_delete()
            await self.db.commit()
        else:
            await self.db.delete(db_obj)
            await self.db.commit()
        return True
