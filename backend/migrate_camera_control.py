from database import engine
from sqlalchemy import text

def run_migration():
    # প্রতিটা ALTER আলাদা connection/transaction এ চালানো হচ্ছে,
    # যাতে একটা fail করলেও অন্যটা normally চলতে পারে (PostgreSQL এ
    # একই transaction এ error হলে পরের command ignore হয়ে যায়)।

    try:
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE camera ADD COLUMN is_enabled BOOLEAN NOT NULL DEFAULT FALSE;"
            ))
            conn.commit()
            print("[OK] 'is_enabled' কলাম যোগ হয়েছে।")
    except Exception as e:
        print(f"[SKIP] 'is_enabled' হয়তো আগে থেকেই আছে: {e}")

    try:
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE camera ADD COLUMN last_heartbeat TIMESTAMP NULL;"
            ))
            conn.commit()
            print("[OK] 'last_heartbeat' কলাম যোগ হয়েছে।")
    except Exception as e:
        print(f"[SKIP] 'last_heartbeat' হয়তো আগে থেকেই আছে: {e}")

if __name__ == "__main__":
    run_migration()
    print("[DONE] Migration শেষ।")