from database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE camera_command ALTER COLUMN course_id DROP NOT NULL;"))
        conn.commit()
    print("[OK] camera_command.course_id এখন nullable হয়েছে।")

if __name__ == "__main__":
    migrate()
