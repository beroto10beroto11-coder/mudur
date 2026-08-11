"""
Converts CP-SAT solver solution to TimetableLesson records.
"""
from ortools.sat.python import cp_model


class ResultBuilder:
    @staticmethod
    def build_lessons(
        solver: cp_model.CpSolver,
        variables: dict,
        assignments: list,
        timeslots: list,
        timetable_id: int,
    ) -> list[dict]:
        lessons = []
        slot_dict = {s.id: s for s in timeslots}

        for (asgn_id, slot_id), var in variables.items():
            if solver.Value(var) == 1:
                asgn = next((a for a in assignments if a.id == asgn_id), None)
                slot = slot_dict.get(slot_id)

                if asgn and slot:
                    lessons.append({
                        "timetable_id": timetable_id,
                        "course_assignment_id": asgn.id,
                        "course_id": asgn.course_id,
                        "teacher_id": asgn.teacher_id,
                        "class_id": asgn.class_id,
                        "classroom_id": asgn.classroom_id,
                        "day": slot.day,
                        "period": slot.period,
                        "is_fixed": asgn.is_fixed,
                    })

        return lessons
