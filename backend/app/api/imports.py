import io
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Response
import pandas as pd
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.database import get_db
from app.models.teacher import Teacher
from app.models.course import Course
from app.models.class_ import ClassGroup
from app.models.classroom import Classroom
from app.models.assignment import CourseAssignment

router = APIRouter(prefix="/imports", tags=["Excel Imports"])


@router.get("/template/{entity_type}")
async def download_import_template(
    entity_type: str,
    current_user: CurrentUser,
):
    """Generate and return a sample Excel template for bulk imports."""
    wb = Workbook()
    ws = wb.active

    if entity_type == "teachers":
        ws.title = "Öğretmenler"
        ws.append(["Ad", "Soyad", "Branş", "E-posta", "Telefon", "Günlük Max Ders"])
        ws.append(["Ahmet", "Yılmaz", "Matematik", "ahmet@okul.com", "05551112233", 8])
        ws.append(["Ayşe", "Kaya", "Fizik", "ayse@okul.com", "05552223344", 8])
    elif entity_type == "classes":
        ws.title = "Sınıflar"
        ws.append(["Sınıf Adı", "Seviye", "Şube", "Öğrenci Sayısı", "Günlük Max Ders"])
        ws.append(["9/A", 9, "A", 30, 8])
        ws.append(["10/B", 10, "B", 32, 8])
    elif entity_type == "courses":
        ws.title = "Dersler"
        ws.append(["Ders Adı", "Ders Kodu", "Branş", "Haftalık Saat", "Blok Ders Saati"])
        ws.append(["Matematik", "MAT", "Matematik", 6, 2])
        ws.append(["Fizik", "FIZ", "Fizik", 4, 2])
    elif entity_type == "classrooms":
        ws.title = "Derslikler"
        ws.append(["Derslik Adı", "Kapasite", "Derslik Türü"])
        ws.append(["Fen Laboratuvarı", 35, "lab_science"])
        ws.append(["Bilişim Sınıfı", 30, "lab_computer"])
    elif entity_type == "assignments":
        ws.title = "Ders Atamaları"
        ws.append(["Sınıf Adı", "Ders Adı", "Öğretmen Ad Soyad", "Özel Derslik", "Haftalık Saat"])
        ws.append(["9/A", "Matematik", "Ahmet Yılmaz", "", 6])
        ws.append(["9/A", "Fizik", "Ayşe Kaya", "Fen Laboratuvarı", 4])
    else:
        raise HTTPException(status_code=400, detail="Geçersiz şablon türü.")

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Sablon_{entity_type}.xlsx"},
    )


@router.post("/teachers")
async def import_teachers(
    school_id: int,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Lütfen geçerli bir Excel dosyası (.xlsx) yükleyin.")

    try:
        df = pd.read_excel(file.file)
    except Exception as e:
        raise HTTPException(400, f"Excel dosyası okunamadı: {e}")

    required_cols = ["Ad", "Soyad"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise HTTPException(400, f"Eksik kolonlar: {', '.join(missing)}")

    created = []
    for _, row in df.iterrows():
        t = Teacher(
            school_id=school_id,
            first_name=str(row["Ad"]).strip(),
            last_name=str(row["Soyad"]).strip(),
            branch=str(row.get("Branş", "")).strip() if pd.notna(row.get("Branş")) else None,
            email=str(row.get("E-posta", "")).strip() if pd.notna(row.get("E-posta")) else None,
            phone=str(row.get("Telefon", "")).strip() if pd.notna(row.get("Telefon")) else None,
            max_daily_hours=int(row.get("Günlük Max Ders", 8)) if pd.notna(row.get("Günlük Max Ders")) else 8,
        )
        db.add(t)
        created.append(t)

    await db.commit()
    return {"message": f"{len(created)} öğretmen başarıyla aktarıldı."}


@router.post("/classes")
async def import_classes(
    school_id: int,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Lütfen geçerli bir Excel dosyası (.xlsx) yükleyin.")

    try:
        df = pd.read_excel(file.file)
    except Exception as e:
        raise HTTPException(400, f"Excel dosyası okunamadı: {e}")

    required_cols = ["Sınıf Adı"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise HTTPException(400, f"Eksik kolonlar: {', '.join(missing)}")

    created = []
    for _, row in df.iterrows():
        name = str(row["Sınıf Adı"]).strip()
        parts = name.split("/")
        grade = int(row.get("Seviye", parts[0] if parts[0].isdigit() else 9))
        section = str(row.get("Şube", parts[1] if len(parts) > 1 else "A")).strip().upper()

        c = ClassGroup(
            school_id=school_id,
            name=name,
            grade=grade,
            section=section,
            student_count=int(row.get("Öğrenci Sayısı", 30)) if pd.notna(row.get("Öğrenci Sayısı")) else 30,
            max_daily_hours=int(row.get("Günlük Max Ders", 8)) if pd.notna(row.get("Günlük Max Ders")) else 8,
        )
        db.add(c)
        created.append(c)

    await db.commit()
    return {"message": f"{len(created)} sınıf başarıyla aktarıldı."}


@router.post("/courses")
async def import_courses(
    school_id: int,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Lütfen geçerli bir Excel dosyası (.xlsx) yükleyin.")

    try:
        df = pd.read_excel(file.file)
    except Exception as e:
        raise HTTPException(400, f"Excel dosyası okunamadı: {e}")

    required_cols = ["Ders Adı"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise HTTPException(400, f"Eksik kolonlar: {', '.join(missing)}")

    created = []
    for _, row in df.iterrows():
        c = Course(
            school_id=school_id,
            name=str(row["Ders Adı"]).strip(),
            code=str(row.get("Ders Kodu", "")).strip().upper() if pd.notna(row.get("Ders Kodu")) else None,
            branch=str(row.get("Branş", "")).strip() if pd.notna(row.get("Branş")) else None,
            weekly_hours=int(row.get("Haftalık Saat", 2)) if pd.notna(row.get("Haftalık Saat")) else 2,
            consecutive_hours=int(row.get("Blok Ders Saati", 1)) if pd.notna(row.get("Blok Ders Saati")) else 1,
        )
        db.add(c)
        created.append(c)

    await db.commit()
    return {"message": f"{len(created)} ders başarıyla aktarıldı."}


@router.post("/classrooms")
async def import_classrooms(
    school_id: int,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Lütfen geçerli bir Excel dosyası (.xlsx) yükleyin.")

    try:
        df = pd.read_excel(file.file)
    except Exception as e:
        raise HTTPException(400, f"Excel dosyası okunamadı: {e}")

    required_cols = ["Derslik Adı"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise HTTPException(400, f"Eksik kolonlar: {', '.join(missing)}")

    created = []
    for _, row in df.iterrows():
        r = Classroom(
            school_id=school_id,
            name=str(row["Derslik Adı"]).strip(),
            capacity=int(row.get("Kapasite", 30)) if pd.notna(row.get("Kapasite")) else 30,
            room_type=str(row.get("Derslik Türü", "normal")).strip() if pd.notna(row.get("Derslik Türü")) else "normal",
        )
        db.add(r)
        created.append(r)

    await db.commit()
    return {"message": f"{len(created)} derslik başarıyla aktarıldı."}


@router.post("/assignments")
async def import_assignments(
    school_id: int,
    academic_year_id: int,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Lütfen geçerli bir Excel dosyası (.xlsx) yükleyin.")

    try:
        df = pd.read_excel(file.file)
    except Exception as e:
        raise HTTPException(400, f"Excel dosyası okunamadı: {e}")

    required_cols = ["Sınıf Adı", "Ders Adı", "Öğretmen Ad Soyad"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise HTTPException(400, f"Eksik kolonlar: {', '.join(missing)}")

    # Pre-load maps for matching names to IDs
    teachers_res = await db.execute(select(Teacher).where(Teacher.school_id == school_id))
    t_map = {t.full_name.lower().strip(): t.id for t in teachers_res.scalars().all()}

    classes_res = await db.execute(select(ClassGroup).where(ClassGroup.school_id == school_id))
    c_map = {c.name.lower().strip(): c.id for c in classes_res.scalars().all()}

    courses_res = await db.execute(select(Course).where(Course.school_id == school_id))
    crs_map = {c.name.lower().strip(): c.id for c in courses_res.scalars().all()}

    rooms_res = await db.execute(select(Classroom).where(Classroom.school_id == school_id))
    r_map = {r.name.lower().strip(): r.id for r in rooms_res.scalars().all()}

    created = []
    skipped = []

    for idx, row in df.iterrows():
        cls_str = str(row["Sınıf Adı"]).lower().strip()
        crs_str = str(row["Ders Adı"]).lower().strip()
        t_str = str(row["Öğretmen Ad Soyad"]).lower().strip()
        r_str = str(row.get("Özel Derslik", "")).lower().strip() if pd.notna(row.get("Özel Derslik")) else ""

        class_id = c_map.get(cls_str)
        course_id = crs_map.get(crs_str)
        teacher_id = t_map.get(t_str)
        classroom_id = r_map.get(r_str) if r_str else None

        if not class_id or not course_id or not teacher_id:
            skipped.append(f"Satır {idx+2}: Sınıf/Ders/Öğretmen veritabanında eşleşmedi ({cls_str}, {crs_str}, {t_str})")
            continue

        weekly_hours = int(row.get("Haftalık Saat", 2)) if pd.notna(row.get("Haftalık Saat")) else 2

        asgn = CourseAssignment(
            school_id=school_id,
            academic_year_id=academic_year_id,
            class_id=class_id,
            course_id=course_id,
            teacher_id=teacher_id,
            classroom_id=classroom_id,
            weekly_hours=weekly_hours,
        )
        db.add(asgn)
        created.append(asgn)

    await db.commit()
    msg = f"{len(created)} ders ataması başarıyla aktarıldı."
    if skipped:
        msg += f" {len(skipped)} satır eşleşmediği için atlandı."
    return {"message": msg, "skipped": skipped}
