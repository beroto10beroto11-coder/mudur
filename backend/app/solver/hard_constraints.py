from ortools.sat.python import cp_model


def add_weekly_hours_constraint(model: cp_model.CpModel, variables: dict, assignments: list, timeslots: list):
    """Each assignment must be scheduled for exactly its weekly_hours."""
    for asgn in assignments:
        asgn_vars = [
            variables[(asgn.id, slot.id)]
            for slot in timeslots
            if (asgn.id, slot.id) in variables
        ]
        if asgn_vars:
            model.Add(sum(asgn_vars) == asgn.weekly_hours)


def add_teacher_conflicts(model: cp_model.CpModel, variables: dict, teachers: list, assignments: list, timeslots: list):
    """No teacher can teach two different lessons at the exact same time slot."""
    for teacher in teachers:
        for slot in timeslots:
            teacher_slot_vars = [
                variables[(asgn.id, slot.id)]
                for asgn in assignments
                if asgn.teacher_id == teacher.id and (asgn.id, slot.id) in variables
            ]
            if len(teacher_slot_vars) > 1:
                model.Add(sum(teacher_slot_vars) <= 1)


def add_class_conflicts(model: cp_model.CpModel, variables: dict, classes: list, assignments: list, timeslots: list):
    """No class group can have two different lessons at the exact same time slot."""
    for cls in classes:
        for slot in timeslots:
            class_slot_vars = [
                variables[(asgn.id, slot.id)]
                for asgn in assignments
                if asgn.class_id == cls.id and (asgn.id, slot.id) in variables
            ]
            if len(class_slot_vars) > 1:
                model.Add(sum(class_slot_vars) <= 1)


def add_classroom_conflicts(model: cp_model.CpModel, variables: dict, classrooms: list, assignments: list, timeslots: list):
    """No classroom can host two different lessons at the exact same time slot."""
    for room in classrooms:
        for slot in timeslots:
            room_slot_vars = [
                variables[(asgn.id, slot.id)]
                for asgn in assignments
                if asgn.classroom_id == room.id and (asgn.id, slot.id) in variables
            ]
            if len(room_slot_vars) > 1:
                model.Add(sum(room_slot_vars) <= 1)


def add_teacher_availability_constraints(model: cp_model.CpModel, variables: dict, availabilities: list, assignments: list, timeslots: list):
    """If a teacher is unavailable at a slot, set that variable to 0."""
    avail_map = {(a.teacher_id, a.day, a.period): a.available for a in availabilities}

    for asgn in assignments:
        for slot in timeslots:
            key = (asgn.teacher_id, slot.day, slot.period)
            if key in avail_map and not avail_map[key]:
                var = variables.get((asgn.id, slot.id))
                if var is not None:
                    model.Add(var == 0)


def add_fixed_lesson_constraints(model: cp_model.CpModel, variables: dict, assignments: list, timeslots: list):
    """If an assignment is fixed to a specific day & period, enforce var == 1."""
    slot_lookup = {(s.day, s.period): s.id for s in timeslots}

    for asgn in assignments:
        if asgn.is_fixed and asgn.fixed_day is not None and asgn.fixed_period is not None:
            target_slot_id = slot_lookup.get((asgn.fixed_day, asgn.fixed_period))
            if target_slot_id:
                var = variables.get((asgn.id, target_slot_id))
                if var is not None:
                    model.Add(var == 1)


def add_daily_limits(model: cp_model.CpModel, variables: dict, teachers: list, classes: list, assignments: list, timeslots: list):
    """Limit max daily hours for teachers and classes."""
    days = set(s.day for s in timeslots)

    for teacher in teachers:
        if teacher.max_daily_hours > 0:
            for d in days:
                daily_vars = [
                    variables[(asgn.id, slot.id)]
                    for asgn in assignments
                    if asgn.teacher_id == teacher.id
                    for slot in timeslots
                    if slot.day == d and (asgn.id, slot.id) in variables
                ]
                if daily_vars:
                    model.Add(sum(daily_vars) <= teacher.max_daily_hours)

    for cls in classes:
        if cls.max_daily_hours > 0:
            for d in days:
                daily_vars = [
                    variables[(asgn.id, slot.id)]
                    for asgn in assignments
                    if asgn.class_id == cls.id
                    for slot in timeslots
                    if slot.day == d and (asgn.id, slot.id) in variables
                ]
                if daily_vars:
                    model.Add(sum(daily_vars) <= cls.max_daily_hours)


def _get_consecutive_hours(asgn) -> int:
    k = getattr(asgn, "consecutive_hours", None)
    if k is not None and k > 1:
        return k
    if "course" in asgn.__dict__ and asgn.__dict__["course"] is not None:
        return getattr(asgn.__dict__["course"], "consecutive_hours", 1)
    return 1


def add_block_lesson_constraints(
    model: cp_model.CpModel,
    variables: dict,
    assignments: list,
    timeslots: list,
):
    """
    Enforce consecutive hours (block lessons) for courses/assignments requiring them.
    E.g. if consecutive_hours == 2, lessons must be scheduled in pairs of contiguous time slots.
    """
    days = set(s.day for s in timeslots)
    slots_by_day = {}
    for d in days:
        slots_by_day[d] = sorted([s for s in timeslots if s.day == d], key=lambda x: x.period)

    for asgn in assignments:
        k = _get_consecutive_hours(asgn)
        if k <= 1:
            continue

        weekly_hours = getattr(asgn, "weekly_hours", 0)
        if weekly_hours < k:
            continue

        is_exact = (weekly_hours % k == 0)

        for d, day_slots in slots_by_day.items():
            n_slots = len(day_slots)
            if n_slots < k:
                continue

            covering_starts = {slot.id: [] for slot in day_slots}

            for i in range(n_slots - k + 1):
                contiguous = True
                for offset in range(k - 1):
                    if day_slots[i + offset + 1].period != day_slots[i + offset].period + 1:
                        contiguous = False
                        break

                if contiguous:
                    start_var = model.NewBoolVar(f"block_start_a{asgn.id}_d{d}_p{day_slots[i].period}")
                    for offset in range(k):
                        target_slot = day_slots[i + offset]
                        covering_starts[target_slot.id].append(start_var)

            for slot in day_slots:
                var = variables.get((asgn.id, slot.id))
                if var is not None:
                    starts = covering_starts[slot.id]
                    if is_exact:
                        if starts:
                            model.Add(var == sum(starts))
                        else:
                            model.Add(var == 0)
                    else:
                        if starts:
                            model.Add(var >= sum(starts))

