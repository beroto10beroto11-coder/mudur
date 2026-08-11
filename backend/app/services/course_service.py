from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.models.course import Course
from app.repositories.course import CourseRepository
from app.schemas.course import CourseCreate, CourseUpdate


class CourseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.course_repo = CourseRepository(db)

    async def get_all_courses(self, school_id: int, skip: int = 0, limit: int = 100) -> list[Course]:
        return await self.course_repo.get_all(school_id=school_id, skip=skip, limit=limit)

    async def get_course(self, course_id: int) -> Course:
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundError("Ders bulunamadı.")
        return course

    async def create_course(self, school_id: int, data: CourseCreate) -> Course:
        data_dict = data.model_dump()
        data_dict["school_id"] = school_id
        return await self.course_repo.create(data_dict)

    async def update_course(self, course_id: int, data: CourseUpdate) -> Course:
        course = await self.get_course(course_id)
        return await self.course_repo.update(course, data.model_dump(exclude_unset=True))

    async def delete_course(self, course_id: int) -> bool:
        return await self.course_repo.delete(course_id, soft=True)
