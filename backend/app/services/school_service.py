from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError, ConflictError
from app.models.school import School, AcademicYear
from app.repositories.school import SchoolRepository, AcademicYearRepository
from app.schemas.school import SchoolCreate, SchoolUpdate, AcademicYearCreate, AcademicYearUpdate


class SchoolService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.school_repo = SchoolRepository(db)
        self.year_repo = AcademicYearRepository(db)

    async def get_all_schools(self, skip: int = 0, limit: int = 100) -> list[School]:
        return await self.school_repo.get_all(skip=skip, limit=limit)

    async def get_school(self, school_id: int) -> School:
        school = await self.school_repo.get_by_id(school_id)
        if not school:
            raise NotFoundError("Okul bulunamadı.")
        return school

    async def create_school(self, data: SchoolCreate) -> School:
        return await self.school_repo.create(data.model_dump())

    async def update_school(self, school_id: int, data: SchoolUpdate) -> School:
        school = await self.get_school(school_id)
        return await self.school_repo.update(school, data.model_dump(exclude_unset=True))

    async def delete_school(self, school_id: int) -> bool:
        return await self.school_repo.delete(school_id, soft=False)

    # Academic Year methods
    async def get_academic_years(self, school_id: int) -> list[AcademicYear]:
        return await self.year_repo.get_all(school_id=school_id)

    async def create_academic_year(self, school_id: int, data: AcademicYearCreate) -> AcademicYear:
        if data.is_active:
            # Set all other years for this school to inactive
            active_year = await self.year_repo.get_active_year(school_id)
            if active_year:
                active_year.is_active = False

        year_dict = data.model_dump()
        year_dict["school_id"] = school_id
        return await self.year_repo.create(year_dict)
