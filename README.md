# 🏫 Okul Ders Programı Yönetim & Otomatik Dağıtım Sistemi

Progmatic benzeri, modern web mimarisine sahip, çoklu okul (multi-tenant) destekli, **Google OR-Tools CP-SAT Constraint Solver** entegreli production-ready okul ders programı yönetim sistemi.

---

## 🚀 Öne Çıkan Özellikler

- **OR-Tools CP-SAT Solver**: Hard & Soft kısıtlamaları tam ayrıştırılmış matematiksel modelleme.
- **Drag & Drop Ders Programı Grid'i**: Sürükle-bırak ders taşıma ve anlık çakışma (conflict) kontrolü.
- **Gerçek Zamanlı Solver İlerlemesi**: Redis Pub/Sub & WebSocket kanalı üzerinden % progress takibi.
- **Multi-Tenant (Çoklu Okul)**: Okullar arası tam veri izolasyonu ve RBAC yetkilendirme.
- **Detaylı Çakışma Analizi**: Çözülemeyen senaryolarda anlaşılır insan dilinde hata raporlaması (`TEACHER_CONFLICT`, `AVAILABILITY_CONFLICT`, `CAPACITY_CONFLICT` vb.).
- **Nöbet & Seçmeli Ders Sistemi**: Otomatik dengeli öğretmen nöbet dağıtımı ve öğrenci seçmeli ders tercih gruplama.
- **Excel & PDF Dışa Aktarım**: Profesyonel biçimlendirilmiş Excel sayfaları ve WeasyPrint ile A4/A3 PDF çıktıları.
- **PostgreSQL Otomatik Yedekleme**: Celery Beat ile her gün 03:00'te `pg_dump` yedeği ve versiyonlama.

---

## 🛠 Mimari & Teknoloji Stack

```text
Frontend: Next.js 14 (App Router), TypeScript, TailwindCSS, TanStack Query, Zustand, dnd-kit
Backend: Python 3.12, FastAPI, SQLAlchemy 2 (Async), Pydantic v2, Alembic
Scheduling: Google OR-Tools CP-SAT Constraint Solver
Queue & Worker: Redis 7, Celery 5 (Solver & Backup kuyrukları)
Database: PostgreSQL 17 (Asyncpg driver)
Exports: pandas, openpyxl, WeasyPrint
Containerization: Docker, docker-compose
```

---

## 📦 Docker ile Hızlı Kurulum (Önerilen)

### 1. Ortam Değişkenlerini Hazırlayın

```bash
cp .env.example .env
```

### 2. Docker Servislerini Çalıştırın

```bash
docker compose up -d --build
```

Bu komut 5 temel servisi ayağa kaldırır:
- **frontend** (`http://localhost:3000`)
- **backend** (`http://localhost:8000`)
- **postgres** (`localhost:5432`)
- **redis** (`localhost:6379`)
- **worker** (Celery background worker)

### 3. Veritabanı Migration & Seed Çalıştırın

```bash
# Migration
docker compose exec backend alembic upgrade head

# Seed Data (Örnek Okul, Öğretmen, Sınıf, Ders ve Atamalar)
docker compose exec backend python scripts/seed.py
```

### 4. Sisteme Giriş Yapın

- **URL**: `http://localhost:3000/login`
- **E-posta**: `admin@school.local`
- **Şifre**: `admin123456`

---

## ⚠️ 'docker' Komutu Bulunamadı Hatası Çözümü

Eğer `docker : The term 'docker' is not recognized` hatası alıyorsanız:

1. **Docker Desktop Yüklü Değilse**:
   - [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) uygulamasını indirin ve kurun.
   - Kurulum tamamlandıktan sonra bilgisayarınızı yeniden başlatın veya PowerShell terminalini kapatıp açın.
   - **Docker Desktop** uygulamasının simgesinin açık (running) durumda olduğundan emin olun.

2. **Docker Olmadan Doğrudan Lokal Çalıştırma (Alternatif)**:

   **Backend (Python):**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

   **Frontend (Next.js):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```


---

## 🧪 Testleri Çalıştırma

Backend unit ve solver doğrulama testleri `pytest` ile yazılmıştır:

```bash
docker compose exec backend pytest tests/ -v
```

Geliştirilmiş testler şunları kapsar:
- **Feasible Dataset**: 5 öğretmen, 5 sınıf, 10 ders, 3 derslik ile başarılı çözülebilir program testi.
- **Impossible Dataset**: Müsaitlik saatlerini aşan imkansız verisetinde solver'ın `INFEASIBLE` ve doğru conflict bilgisi döndürme testi.

---

## 📖 API Dokümantasyonu

FastAPI Swagger ve ReDoc dokümantasyonu otomatik aktiftir:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 📂 Proje Dizin Yapısı

```text
mudur/
├── backend/
│   ├── alembic/              # Alembic migration scripts
│   ├── app/
│   │   ├── api/              # REST & WebSocket API endpoints
│   │   ├── auth/             # JWT & Argon2 auth handlers
│   │   ├── core/             # Config, Database, Redis, Exceptions, Logging
│   │   ├── models/           # SQLAlchemy 2 Async ORM Models
│   │   ├── repositories/     # Database CRUD Repositories
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   ├── services/         # Business logic layer
│   │   ├── solver/           # OR-Tools CP-SAT Timetable Engine
│   │   └── tasks/            # Celery async tasks (Solver & Backup)
│   ├── scripts/              # Seed scripts
│   ├── tests/                # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/                  # Next.js 14 App Router Pages
│   ├── components/           # UI Components (Sidebar, Navbar, TimetableGrid)
│   ├── lib/                  # API client (Axios with JWT interceptors)
│   ├── stores/               # Zustand global state (Auth, Active School)
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```
