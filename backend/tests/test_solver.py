import pytest
from app.solver.engine import TimetableSolver


class DummyObj:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.mark.asyncio
async def test_solver_feasible_dataset():
    """Test solver with 5 teachers, 5 classes, 10 courses, 3 classrooms, 5 days x 6 periods."""
    teachers = [DummyObj(id=i, full_name=f"Teacher {i}", max_daily_hours=6) for i in range(1, 6)]
    classes = [DummyObj(id=i, name=f"{9+i}/A", max_daily_hours=6, student_count=30) for i in range(1, 6)]
    classrooms = [DummyObj(id=i, name=f"Room {i}", capacity=35, room_type="normal") for i in range(1, 4)]

    # Time slots: 5 days x 6 periods = 30 slots
    timeslots = []
    slot_id = 1
    for day in range(5):
        for period in range(1, 7):
            timeslots.append(DummyObj(id=slot_id, day=day, period=period))
            slot_id += 1

    # Assignments: Total 15 assignments, each 2 hours = 30 total hours per class
    assignments = []
    asgn_id = 1
    for c_idx in range(1, 6):
        for sub_idx in range(1, 4):
            t_id = ((c_idx + sub_idx) % 5) + 1
            r_id = (asgn_id % 3) + 1
            assignments.append(
                DummyObj(
                    id=asgn_id,
                    course_id=sub_idx,
                    teacher_id=t_id,
                    class_id=c_idx,
                    classroom_id=r_id,
                    weekly_hours=2,
                    is_fixed=False,
                )
            )
            asgn_id += 1

    solver = TimetableSolver(
        assignments=assignments,
        teachers=teachers,
        classes=classes,
        classrooms=classrooms,
        timeslots=timeslots,
        availabilities=[],
        timetable_id=1,
    )

    result = solver.solve(max_time_seconds=10)
    assert result["success"] is True
    assert len(result["lessons"]) > 0
    assert result["status"] in ("OPTIMAL", "FEASIBLE")


@pytest.mark.asyncio
async def test_solver_impossible_dataset():
    """Test solver with an intentionally impossible dataset (too many hours for available slots)."""
    teachers = [DummyObj(id=1, full_name="Teacher 1", max_daily_hours=6)]
    classes = [DummyObj(id=1, name="9/A", max_daily_hours=6, student_count=30)]
    classrooms = [DummyObj(id=1, name="Room 1", capacity=35, room_type="normal")]

    # Time slots: 5 days x 2 periods = 10 slots
    timeslots = []
    slot_id = 1
    for day in range(5):
        for period in range(1, 3):
            timeslots.append(DummyObj(id=slot_id, day=day, period=period))
            slot_id += 1

    # Assignment requiring 20 hours (when only 10 slots exist!)
    assignments = [
        DummyObj(
            id=1,
            course_id=1,
            teacher_id=1,
            class_id=1,
            classroom_id=1,
            weekly_hours=20,
            is_fixed=False,
        )
    ]

    solver = TimetableSolver(
        assignments=assignments,
        teachers=teachers,
        classes=classes,
        classrooms=classrooms,
        timeslots=timeslots,
        availabilities=[],
        timetable_id=1,
    )

    result = solver.solve(max_time_seconds=5)
    assert result["success"] is False
    assert result["status"] == "INFEASIBLE"
    assert len(result["conflicts"]) > 0


@pytest.mark.asyncio
async def test_solver_block_lessons():
    """Test that assignments with consecutive_hours=2 are scheduled in 2-period contiguous blocks."""
    teachers = [DummyObj(id=1, full_name="Teacher 1", max_daily_hours=6)]
    classes = [DummyObj(id=1, name="9/A", max_daily_hours=6, student_count=30)]
    classrooms = [DummyObj(id=1, name="Room 1", capacity=35, room_type="normal")]

    # Time slots: 5 days x 8 periods
    timeslots = []
    slot_id = 1
    for day in range(5):
        for period in range(1, 9):
            timeslots.append(DummyObj(id=slot_id, day=day, period=period))
            slot_id += 1

    # Course with 2-hour consecutive requirement
    course_lab = DummyObj(id=1, name="Science Lab", consecutive_hours=2)

    # 4 weekly hours = 2 blocks of 2 hours
    assignments = [
        DummyObj(
            id=1,
            course_id=1,
            course=course_lab,
            teacher_id=1,
            class_id=1,
            classroom_id=1,
            weekly_hours=4,
            consecutive_hours=2,
            is_fixed=False,
        )
    ]

    solver = TimetableSolver(
        assignments=assignments,
        teachers=teachers,
        classes=classes,
        classrooms=classrooms,
        timeslots=timeslots,
        availabilities=[],
        timetable_id=1,
    )

    result = solver.solve(max_time_seconds=5)
    assert result["success"] is True
    lessons = result["lessons"]
    assert len(lessons) == 4

    # Group lessons by day
    by_day = {}
    for l in lessons:
        by_day.setdefault(l["day"], []).append(l["period"])

    # Verify that on every day where lessons appear, periods form contiguous pairs of length 2
    for day, periods in by_day.items():
        periods.sort()
        assert len(periods) == 2, f"Day {day} should have exactly 2 hours (1 block)"
        assert periods[1] == periods[0] + 1, f"Periods on day {day} must be contiguous: {periods}"

