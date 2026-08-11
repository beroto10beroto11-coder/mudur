import os
import sys
import sqlite3

def apply_sqlite_migrations(db_path: str = "school_scheduler.db"):
    possible_paths = [
        "school_scheduler.db",
        "backend/school_scheduler.db",
        os.path.join(os.getcwd(), "school_scheduler.db"),
        os.path.join(os.getcwd(), "backend", "school_scheduler.db"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "school_scheduler.db"),
    ]
    target_paths = list(set([p for p in possible_paths if os.path.exists(p)]))
    
    for path in target_paths:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        # 1. Teachers table columns
        cursor.execute("PRAGMA table_info('teachers')")
        t_cols = [r[1] for r in cursor.fetchall()]
        if t_cols:
            if "allowed_courses" not in t_cols:
                cursor.execute("ALTER TABLE teachers ADD COLUMN allowed_courses VARCHAR(500) DEFAULT 'ALL'")
                print(f"[+] Added column 'allowed_courses' to 'teachers' table in {path}.")
            if "allowed_classes" not in t_cols:
                cursor.execute("ALTER TABLE teachers ADD COLUMN allowed_classes VARCHAR(500) DEFAULT 'ALL'")
                print(f"[+] Added column 'allowed_classes' to 'teachers' table in {path}.")

        # 2. Courses table columns
        cursor.execute("PRAGMA table_info('courses')")
        c_cols = [r[1] for r in cursor.fetchall()]
        if c_cols:
            if "target_classes" not in c_cols:
                cursor.execute("ALTER TABLE courses ADD COLUMN target_classes VARCHAR(255) DEFAULT 'ALL'")
                print(f"[+] Added column 'target_classes' to 'courses' table in {path}.")
            if "hour_distribution" not in c_cols:
                cursor.execute("ALTER TABLE courses ADD COLUMN hour_distribution VARCHAR(255) DEFAULT '2+2+1+1'")
                print(f"[+] Added column 'hour_distribution' to 'courses' table in {path}.")

        conn.commit()
        conn.close()
    print("[OK] SQLite schema migrations applied successfully.")

if __name__ == "__main__":
    db_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "school_scheduler.db")
    apply_sqlite_migrations(db_file)
