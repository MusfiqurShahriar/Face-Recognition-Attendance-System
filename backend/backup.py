from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import os
import subprocess
import pickle

load_dotenv(find_dotenv())

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
OAUTH_FILE = "oauth_credentials.json"
TOKEN_FILE = "token.pickle"
FOLDER_ID = "1HwEo4H_TA4-meNovsmUzyYoN0rzrSiLx"

PG_DUMP_PATH = r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe"

BACKUP_DIR = "../database/backups"

raw_db_url = os.getenv("DATABASE_URL", "")
if raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = raw_db_url

def get_drive_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(OAUTH_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)
    return build("drive", "v3", credentials=creds)

def upload_to_drive(file_path, file_name):
    try:
        service = get_drive_service()

        file_metadata = {
            "name": file_name,
            "parents": [FOLDER_ID]
        }
        media = MediaFileUpload(file_path, mimetype="application/octet-stream")

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        print(f"[OK] Google Drive এ backup হয়েছে → {file_name}")
        return True
    except Exception as e:
        print(f"[ERROR] Backup failed — {e}")
        return False

def create_backup():
    if not DATABASE_URL:
        print("[ERROR] .env এ DATABASE_URL পাওয়া যায়নি, backup নেওয়া সম্ভব না")
        return False

    if not os.path.exists(PG_DUMP_PATH):
        print(f"[ERROR] pg_dump পাওয়া যায়নি এই path এ: {PG_DUMP_PATH}")
        return False

    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    backup_name = f"neon_backup_{now}.sql"

    os.makedirs(BACKUP_DIR, exist_ok=True)
    local_backup = os.path.join(BACKUP_DIR, backup_name)

    print(f"[INFO] Neon database থেকে backup নেওয়া শুরু হচ্ছে...")

    try:
        result = subprocess.run(
            [PG_DUMP_PATH, DATABASE_URL, "--file", local_backup, "--format", "plain"],
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode != 0:
            print(f"[ERROR] pg_dump ব্যর্থ হয়েছে:\n{result.stderr}")
            return False

        print(f"[OK] Local backup তৈরি হয়েছে → {local_backup}")

    except subprocess.TimeoutExpired:
        print("[ERROR] pg_dump timeout হয়ে গেছে (10 মিনিটের বেশি সময় লেগেছে)")
        return False
    except Exception as e:
        print(f"[ERROR] pg_dump চালাতে সমস্যা হয়েছে: {e}")
        return False

    result = upload_to_drive(local_backup, backup_name)
    backups = sorted(
        f for f in os.listdir(BACKUP_DIR) if f.startswith("neon_backup_") and f.endswith(".sql")
    )
    if len(backups) > 7:
        for old in backups[:-7]:
            os.remove(os.path.join(BACKUP_DIR, old))
            print(f"[OK] পুরনো backup মুছা হয়েছে → {old}")

    return result

if __name__ == "__main__":
    create_backup()