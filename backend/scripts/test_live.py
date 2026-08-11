import json
import urllib.request


def test_live_workflow():
    base_url = "http://localhost:8000/api"

    # 1. Login
    login_data = json.dumps({
        "email": "admin@school.k12.tr",
        "password": "admin123456",
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/auth/login",
        data=login_data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as response:
        login_res = json.loads(response.read().decode("utf-8"))
        token = login_res["access_token"]
        print("[OK] Login successful! JWT Access Token acquired.")

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Teachers
    req = urllib.request.Request(f"{base_url}/teachers?school_id=1", headers=headers)
    with urllib.request.urlopen(req) as response:
        teachers = json.loads(response.read().decode("utf-8"))
        print(f"[OK] Teachers endpoint working! Found {len(teachers)} teachers.")

    # 3. Get Classes
    req = urllib.request.Request(f"{base_url}/classes?school_id=1", headers=headers)
    with urllib.request.urlopen(req) as response:
        classes = json.loads(response.read().decode("utf-8"))
        print(f"[OK] Classes endpoint working! Found {len(classes)} classes.")

    # 4. Generate Timetable via OR-Tools Solver
    gen_data = json.dumps({
        "academic_year_id": 1,
        "name": "Live Test Timetable",
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/timetables/generate?school_id=1",
        data=gen_data,
        headers={"Content-Type": "application/json", **headers},
    )
    with urllib.request.urlopen(req) as response:
        tt = json.loads(response.read().decode("utf-8"))
        tt_id = tt["id"]
        print(f"[OK] Timetable generation triggered! Timetable ID: {tt_id}, Status: {tt['status']}")

    import time
    time.sleep(2)

    # 5. Get Timetable Lessons
    req = urllib.request.Request(f"{base_url}/timetables/{tt_id}/lessons", headers=headers)
    with urllib.request.urlopen(req) as response:
        lessons = json.loads(response.read().decode("utf-8"))
        print(f"[OK] Timetable grid lessons retrieved! Total scheduled lessons: {len(lessons)}")


if __name__ == "__main__":
    test_live_workflow()
