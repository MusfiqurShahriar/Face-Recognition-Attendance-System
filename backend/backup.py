from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime
import os
import shutil
import pickle

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
OAUTH_FILE = "oauth_credentials.json"
TOKEN_FILE = "token.pickle"
FOLDER_ID = "1HwEo4H_TA4-meNovsmUzyYoN0rzrSiLx"
DB_PATH = "../database/attendance.db"
BACKUP_DIR = "../database/backups"

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
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    backup_name = f"attendance_backup_{now}.db"

    os.makedirs(BACKUP_DIR, exist_ok=True)
    local_backup = os.path.join(BACKUP_DIR, backup_name)
    shutil.copy2(DB_PATH, local_backup)
    print(f"[OK] Local backup তৈরি হয়েছে → {local_backup}")

    result = upload_to_drive(local_backup, backup_name)
    backups = sorted(os.listdir(BACKUP_DIR))
    if len(backups) > 7:
        for old in backups[:-7]:
            os.remove(os.path.join(BACKUP_DIR, old))
            print(f"[OK] পুরনো backup মুছা হয়েছে → {old}")
    return result

if __name__ == "__main__":
    create_backup()