"""
Analyzes infeasible timetable problems to generate human-readable conflict reports.
"""
from typing import Any


class ConflictAnalyzer:
    @staticmethod
    def analyze(
        teachers: list,
        classes: list,
        classrooms: list,
        assignments: list,
        timeslots: list,
        availabilities: list,
    ) -> list[dict[str, Any]]:
        conflicts: list[dict[str, Any]] = []
        total_slots = len(timeslots)

        # 1. Total weekly hours vs Total available slots per class
        slot_count = len(timeslots)
        for cls in classes:
            class_assignments = [a for a in assignments if a.class_id == cls.id]
            total_hours = sum(a.weekly_hours for a in class_assignments)
            if total_hours > slot_count:
                conflicts.append({
                    "type": "WEEKLY_HOURS_CONFLICT",
                    "entity": f"Sınıf: {cls.name}",
                    "message": f"{cls.name} sınıfının haftalık ders saati ({total_hours} saat), mevcut zaman diliminden ({slot_count} saat) fazla.",
                })

        # 2. Teacher availability vs Assigned hours
        avail_map = {}
        for a in availabilities:
            if not a.available:
                avail_map[(a.teacher_id, a.day, a.period)] = False

        for teacher in teachers:
            teacher_assignments = [a for a in assignments if a.teacher_id == teacher.id]
            total_required = sum(a.weekly_hours for a in teacher_assignments)
            unavailable_count = sum(
                1 for s in timeslots if (teacher.id, s.day, s.period) in avail_map
            )
            available_slots = slot_count - unavailable_count

            if total_required > available_slots:
                conflicts.append({
                    "type": "AVAILABILITY_CONFLICT",
                    "entity": f"Öğretmen: {teacher.full_name}",
                    "message": f"{teacher.full_name} öğretmenin haftalık ders yükü ({total_required} saat), uygun saatlerinden ({available_slots} saat) fazla.",
                })

        # 3. Classroom capacity & requirements
        for room in classrooms:
            room_assignments = [a for a in assignments if a.classroom_id == room.id]
            for asgn in room_assignments:
                target_class = next((c for c in classes if c.id == asgn.class_id), None)
                if target_class and target_class.student_count > room.capacity:
                    conflicts.append({
                        "type": "CAPACITY_CONFLICT",
                        "entity": f"Derslik: {room.name}",
                        "message": f"{room.name} dersliğinin kapasitesi ({room.capacity}), {target_class.name} sınıfının öğrenci sayısından ({target_class.student_count}) düşük.",
                    })

        if not conflicts:
            conflicts.append({
                "type": "GENERAL_INFEASIBILITY",
                "entity": "Sistem",
                "message": "Belirtilen kısıtlar altında geçerli bir ders programı bulunamadı. Lütfen öğretmen kapalı saatlerini veya ders atamalarını esnetin.",
            })

        return conflicts
