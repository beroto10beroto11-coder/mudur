"""
Main TimetableSolver Engine integrating OR-Tools CP-SAT.
"""
import time
from typing import Callable, Any
from ortools.sat.python import cp_model

from app.solver.config import SolverConfig
from app.solver.hard_constraints import (
    add_weekly_hours_constraint,
    add_teacher_conflicts,
    add_class_conflicts,
    add_classroom_conflicts,
    add_teacher_availability_constraints,
    add_fixed_lesson_constraints,
    add_daily_limits,
    add_block_lesson_constraints,
)
from app.solver.soft_constraints import add_soft_objectives
from app.solver.conflict_analyzer import ConflictAnalyzer
from app.solver.result_builder import ResultBuilder


class SolverCallback(cp_model.CpSolverSolutionCallback):
    """Callback to report real-time progress during solving."""

    def __init__(self, progress_callback: Callable[[dict[str, Any]], None] | None = None):
        super().__init__()
        self._progress_callback = progress_callback
        self._solution_count = 0
        self._start_time = time.time()

    def on_solution_callback(self):
        self._solution_count += 1
        elapsed = time.time() - self._start_time
        if self._progress_callback:
            self._progress_callback({
                "percent": min(95, self._solution_count * 20),
                "solution_count": self._solution_count,
                "elapsed_seconds": round(elapsed, 2),
                "objective_value": self.ObjectiveValue(),
            })


class TimetableSolver:
    def __init__(
        self,
        assignments: list,
        teachers: list,
        classes: list,
        classrooms: list,
        timeslots: list,
        availabilities: list,
        timetable_id: int,
    ):
        self.model = cp_model.CpModel()
        self.assignments = assignments
        self.teachers = teachers
        self.classes = classes
        self.classrooms = classrooms
        self.timeslots = timeslots
        self.availabilities = availabilities
        self.timetable_id = timetable_id
        self.variables: dict[tuple[int, int], cp_model.BoolVar] = {}

    def _create_variables(self):
        for asgn in self.assignments:
            for slot in self.timeslots:
                var_name = f"x_a{asgn.id}_s{slot.id}"
                self.variables[(asgn.id, slot.id)] = self.model.NewBoolVar(var_name)

    def solve(
        self,
        max_time_seconds: int = SolverConfig.MAX_TIME_IN_SECONDS,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        start_time = time.time()

        # 1. Create decision variables
        self._create_variables()

        # 2. Add Hard Constraints
        add_weekly_hours_constraint(self.model, self.variables, self.assignments, self.timeslots)
        add_teacher_conflicts(self.model, self.variables, self.teachers, self.assignments, self.timeslots)
        add_class_conflicts(self.model, self.variables, self.classes, self.assignments, self.timeslots)
        add_classroom_conflicts(self.model, self.variables, self.classrooms, self.assignments, self.timeslots)
        add_teacher_availability_constraints(self.model, self.variables, self.availabilities, self.assignments, self.timeslots)
        add_fixed_lesson_constraints(self.model, self.variables, self.assignments, self.timeslots)
        add_daily_limits(self.model, self.variables, self.teachers, self.classes, self.assignments, self.timeslots)
        add_block_lesson_constraints(self.model, self.variables, self.assignments, self.timeslots)


        # 3. Add Soft Constraints (Optimization Objectives)
        add_soft_objectives(
            self.model,
            self.variables,
            self.teachers,
            self.classes,
            self.assignments,
            self.timeslots,
            self.availabilities,
        )

        # 4. Configure CP-SAT Solver with High Performance Parameters
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_time_seconds
        solver.parameters.num_search_workers = SolverConfig.NUM_SEARCH_WORKERS
        solver.parameters.search_branching = cp_model.PORTFOLIO_SEARCH
        solver.parameters.linearization_level = SolverConfig.LINEARIZATION_LEVEL
        solver.parameters.cp_model_presolve = True

        callback = SolverCallback(progress_callback)

        # 5. Solve
        status = solver.Solve(self.model, callback)
        duration = time.time() - start_time

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            lessons = ResultBuilder.build_lessons(
                solver, self.variables, self.assignments, self.timeslots, self.timetable_id
            )
            return {
                "success": True,
                "status": "FEASIBLE" if status == cp_model.FEASIBLE else "OPTIMAL",
                "duration_seconds": round(duration, 2),
                "objective_value": solver.ObjectiveValue(),
                "lessons": lessons,
                "conflicts": [],
            }
        else:
            conflicts = ConflictAnalyzer.analyze(
                self.teachers,
                self.classes,
                self.classrooms,
                self.assignments,
                self.timeslots,
                self.availabilities,
            )
            return {
                "success": False,
                "status": "INFEASIBLE",
                "duration_seconds": round(duration, 2),
                "objective_value": None,
                "lessons": [],
                "conflicts": conflicts,
            }
