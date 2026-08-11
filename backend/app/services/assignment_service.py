from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.models.assignment import CourseAssignment
from app.repositories.assignment import CourseAssignmentRepository
from app.schemas.assignment import CourseAssignmentCreate, CourseAssignmentUpdate


class CourseAssignmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.assignment_repo = CourseAssignmentRepository(db)

    async def get_assignments(self, school_id: int, academic_year_id: int) -> list[CourseAssignment]:
        return await self.assignment_repo.get_all_with_relations(school_id, academic_year_id)

    async def get_assignment(self, assignment_id: int) -> CourseAssignment:
        asgn = await self.assignment_repo.get_by_id(assignment_id)
        if not asgn:
            raise NotFoundError("Ders ataması bulunamadı.")
        return asgn

    async def create_assignment(self, school_id: int, data: CourseAssignmentCreate) -> CourseAssignment:
        data_dict = data.model_dump()
        data_dict["school_id"] = school_id
        return await self.assignment_repo.create(data_dict)

    async def update_assignment(self, assignment_id: int, data: CourseAssignmentUpdate) -> CourseAssignment:
        asgn = await self.get_assignment(assignment_id)
        return await self.assignment_repo.update(asgn, data.model_dump(exclude_unset=True))

    async def delete_assignment(self, assignment_id: int) -> bool:
        return await self.assignment_repo.delete(assignment_id, soft=False)
