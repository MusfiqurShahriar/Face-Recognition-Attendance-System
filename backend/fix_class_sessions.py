from sqlalchemy import text
from database import engine

def migrate():
    with engine.connect() as conn:
        for col_name, col_type in [("course_id", "INTEGER"), ("session_id", "INTEGER")]:
            try:
                conn.execute(text(f"ALTER TABLE class_sessions ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"যোগ হলো: class_sessions.{col_name}")
            except Exception as e:
                conn.rollback()
                print(f"Skip (class_sessions.{col_name}): {e}")
if __name__ == "__main__":
    migrate()