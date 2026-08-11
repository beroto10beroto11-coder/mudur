from ortools.sat.python import cp_model
from app.solver.config import ConstraintPriority


def add_soft_objectives(
    model: cp_model.CpModel,
    variables: dict,
    teachers: list,
    classes: list,
    assignments: list,
    timeslots: list,
    availabilities: list,
):
    """
    Build soft constraint penalties to optimize schedule quality:
    - Minimize teacher gaps
    - Minimize class gaps
    - Respect teacher preferences
    - Balance daily load
    """
    penalties = []
    days = sorted(list(set(s.day for s in timeslots)))
    periods_by_day = {}
    for d in days:
        periods_by_day[d] = sorted([s for s in timeslots if s.day == d], key=lambda x: x.period)

    # 1. Teacher Preferences (preferred +1, disliked -1, strongly disliked -2)
    pref_map = {(a.teacher_id, a.day, a.period): a.preference for a in availabilities}
    for asgn in assignments:
        for slot in timeslots:
            key = (asgn.teacher_id, slot.day, slot.period)
            pref = pref_map.get(key, 0)
            var = variables.get((asgn.id, slot.id))
            if var is not None:
                if pref < 0:
                    # Penalty for assigning in disliked slot
                    penalty_weight = abs(pref) * ConstraintPriority.NORMAL
                    penalties.append(var * penalty_weight)
                elif pref > 0:
                    # Reward (negative penalty) for assigning in preferred slot
                    reward_weight = pref * ConstraintPriority.NORMAL
                    penalties.append(var * (-reward_weight))

    # 2. Minimize Teacher Gaps (Windowing / Boşluk Önleme)
    for teacher in teachers:
        for d in days:
            slots_in_day = periods_by_day.get(d, [])
            if len(slots_in_day) < 3:
                continue

            for i in range(len(slots_in_day) - 2):
                s1, s2, s3 = slots_in_day[i], slots_in_day[i + 1], slots_in_day[i + 2]

                # Check if teacher has lesson at s1 and s3 but NOT s2
                v1 = [variables[(a.id, s1.id)] for a in assignments if a.teacher_id == teacher.id and (a.id, s1.id) in variables]
                v2 = [variables[(a.id, s2.id)] for a in assignments if a.teacher_id == teacher.id and (a.id, s2.id) in variables]
                v3 = [variables[(a.id, s3.id)] for a in assignments if a.teacher_id == teacher.id and (a.id, s3.id) in variables]

                if v1 and v2 and v3:
                    gap_var = model.NewBoolVar(f"teacher_gap_{teacher.id}_d{d}_p{s2.period}")
                    # gap_var == True IF v1_sum > 0 AND v3_sum > 0 AND v2_sum == 0
                    model.Add(sum(v1) + sum(v3) - sum(v2) <= 1 + gap_var)
                    penalties.append(gap_var * ConstraintPriority.IMPORTANT)

    # Minimize sum of all penalties
    if penalties:
        model.Minimize(sum(penalties))
