import time
import face_recognition
import cv2
import pickle
import numpy as np
import requests
from datetime import datetime
import json
import os
import threading
import onnxruntime as ort

ENCODINGS_FILE = "../models/encodings.pkl"
ANTI_SPOOF_MODEL_PATH = "../models/anti_spoof_model.onnx"
OFFLINE_FILE = "offline_queue.json"

TOLERANCE = 0.45
CURRENT_SEMESTER = None

from dotenv import load_dotenv
load_dotenv()

BASE_URL = os.getenv("SERVER_BASE_URL", "https://face-recognition-attendance-system-yuhz.onrender.com")
SERVER_URL = f"{BASE_URL}/api/mark-attendance"
POLL_URL = f"{BASE_URL}/api/camera-command"
CAMERA_CODE = None  # শুরুতে জিজ্ঞেস করা হবে

active_course_id = None
active_session_id = None

# ==========================================
# Shared State (Thread-safe)
# ==========================================
already_marked = set()
already_printed = set()
marked_lock = threading.Lock()

# ==========================================
# Encoding Load
# ==========================================
print("[INFO] Encoding লোড হচ্ছে...")
with open(ENCODINGS_FILE, "rb") as f:
    data = pickle.load(f)

known_encodings = data["encodings"]
known_names = data["names"]
known_roles = data["roles"]

ROLE_COLORS = {
    "students": (0, 255, 0),
    "teachers": (255, 165, 0),
    "Unknown":  (0, 0, 255),
    "Spoof":    (0, 0, 200)
}

# ==========================================
# Anti-Spoof Model Load
# ==========================================
print("[INFO] Anti-spoof model লোড হচ্ছে...")
antispoof_session = ort.InferenceSession(ANTI_SPOOF_MODEL_PATH, providers=["CPUExecutionProvider"])
antispoof_input_name = antispoof_session.get_inputs()[0].name
print("[OK] Anti-spoof model লোড হয়েছে।")

# ==========================================
# Anti-Spoof Function (Deep Learning Model)
# ==========================================
def _get_crop_box(src_w, src_h, bbox, scale):
    """
    bbox: (x, y, w, h) — face box (top-left corner + width/height)
    scale: কত গুণ বড় area crop করতে হবে (এই model এর জন্য 2.7)
    """
    x, y, box_w, box_h = bbox
    scale = min((src_h - 1) / box_h, min((src_w - 1) / box_w, scale))

    new_width = box_w * scale
    new_height = box_h * scale
    center_x = box_w / 2 + x
    center_y = box_h / 2 + y

    left = center_x - new_width / 2
    top = center_y - new_height / 2
    right = center_x + new_width / 2
    bottom = center_y + new_height / 2

    if left < 0:
        right -= left
        left = 0
    if top < 0:
        bottom -= top
        top = 0
    if right > src_w - 1:
        left -= (right - src_w + 1)
        right = src_w - 1
    if bottom > src_h - 1:
        top -= (bottom - src_h + 1)
        bottom = src_h - 1

    return int(left), int(top), int(right), int(bottom)


def is_real_face(face_img, full_frame=None, face_box_xywh=None):
    """
    face_img: fallback হিসেবে ব্যবহার হবে যদি full_frame/box দেওয়া না থাকে
    full_frame + face_box_xywh (x, y, w, h) দিলে সবচেয়ে ভালো accuracy পাওয়া যাবে,
    কারণ model-টা face এর চারপাশে extra context (2.7x area) দেখে ট্রেইন হয়েছে।

    Returns: True if real face, False if spoof
    """
    return True 
    try:
        if full_frame is not None and face_box_xywh is not None:
            src_h, src_w = full_frame.shape[:2]
            left, top, right, bottom = _get_crop_box(src_w, src_h, face_box_xywh, scale=2.7)
            cropped = full_frame[top:bottom + 1, left:right + 1]
        else:
            cropped = face_img

        if cropped is None or cropped.size == 0:
            return True

        
        cv2.imwrite("debug_crop.jpg", cropped)
        print(f"[DEBUG] cropped shape={cropped.shape}, box={face_box_xywh}")

        resized = cv2.resize(cropped, (80, 80))
        resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        # Model 0-1 range float32 চায়, BGR order ঠিক রেখে (cv2 default)
        input_tensor = resized.astype(np.float32) / 255.0
        input_tensor = np.transpose(input_tensor, (2, 0, 1))  # HWC -> CHW
        input_tensor = np.expand_dims(input_tensor, axis=0)   # add batch dim

        outputs = antispoof_session.run(None, {antispoof_input_name: input_tensor})
        logits = outputs[0][0]

        # Softmax
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / exp_logits.sum()

        label_idx = int(np.argmax(probs))
        print(f"[DEBUG] probs={probs}  label_idx={label_idx}")

        # Index 1 = Real (model convention অনুযায়ী)
        is_real = (label_idx == 1)

        return is_real
    except Exception as e:
        print(f"[WARNING] Anti-spoof check failed: {e}")
        return True

# ==========================================
# Offline Sync Functions
# ==========================================
def save_offline(payload):
    queue = []
    if os.path.exists(OFFLINE_FILE):
        try:
            with open(OFFLINE_FILE, "r") as f:
                queue = json.load(f)
        except:
            pass

    if payload not in queue:
        queue.append(payload)
        with open(OFFLINE_FILE, "w") as f:
            json.dump(queue, f, indent=4)

def sync_offline():
    if not os.path.exists(OFFLINE_FILE):
        return
    try:
        with open(OFFLINE_FILE, "r") as f:
            queue = json.load(f)
    except:
        return
    if not queue:
        return

    print(f"\n[INFO] {len(queue)} টি অফলাইন ডেটা আপলোড হচ্ছে...")
    unsynced = []
    for payload in queue:
        try:
            res = requests.post(SERVER_URL, json=payload, timeout=10)
            if res.status_code != 200:
                unsynced.append(payload)
        except:
            unsynced.append(payload)
            break

    if unsynced:
        with open(OFFLINE_FILE, "w") as f:
            json.dump(unsynced, f, indent=4)
        print(f"[INFO] {len(unsynced)} টি ডেটা আপলোড করা যায়নি।")
    else:
        if os.path.exists(OFFLINE_FILE):
            os.remove(OFFLINE_FILE)
        print("[INFO] সব অফলাইন ডেটা আপলোড হয়েছে!\n")

# Attendance Marking
def mark_attendance(name, role):
    if active_course_id is None:
        return "Waiting for Course"
    payload = {
        "name": name,
        "role": role.rstrip("s"),
        "semester": CURRENT_SEMESTER,
        "course_id": active_course_id,
        "session_id": active_session_id
    }
    try:
        response = requests.post(SERVER_URL, json=payload, timeout=10)
        if response.status_code == 200:
            result_data = response.json()
            db_status = result_data.get("status")
            if db_status == "duplicate":
                return "Already Marked"
            elif db_status == "success":
                sync_offline()
                return result_data.get("status_message", "Present")
            else:
                return "Failed"
        else:
            return f"Server Error ({response.status_code})"
    except requests.exceptions.RequestException:
        save_offline(payload)
        return "Saved Offline"

def poll_camera_command():
    global active_course_id, active_session_id
    while True:
        try:
            res = requests.get(f"{POLL_URL}/{CAMERA_CODE}", timeout=5)
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "success":
                    new_course = data.get("course_id")
                    if new_course != active_course_id:
                        active_course_id = new_course
                        active_session_id = data.get("session_id")
                        print(f"\n[COMMAND] নতুন Course activate হলো: {data.get('course_code')} (course_id={active_course_id})\n")
        except requests.exceptions.RequestException:
            pass
        time.sleep(5)

# ==========================================
# Camera Thread
# ==========================================
def camera_thread(camera_source, camera_name, window_name):
    print(f"[INFO] {camera_name} চালু হচ্ছে...")
    cap = cv2.VideoCapture(camera_source)

    if not cap.isOpened():
        print(f"[ERROR] {camera_name} খুলতে পারেনি!")
        return

    print(f"[OK] {camera_name} চালু হয়েছে।")

    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"[ERROR] {camera_name} থেকে frame পাওয়া যাচ্ছে না!")
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        face_roles = []
        face_statuses = []

        for face_encoding, face_location in zip(face_encodings, face_locations):

            # Anti-Spoof Check
            top, right, bottom, left = [x * 4 for x in face_location]
            face_img = frame[top:bottom, left:right]
            box_xywh = (left, top, right - left, bottom - top)
            real = is_real_face(face_img, full_frame=frame, face_box_xywh=box_xywh)

            if not real:
                face_names.append("Spoof!")
                face_roles.append("Spoof")
                face_statuses.append("⚠️ FAKE")
                print(f"[ALERT] {camera_name}: Spoof attempt detected!")
                continue

            # Face Recognition
            matches = face_recognition.compare_faces(
                known_encodings, face_encoding, tolerance=TOLERANCE
            )
            name = "Unknown"
            role = "Unknown"

            face_distances = face_recognition.face_distance(known_encodings, face_encoding)

            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index] and face_distances[best_match_index] <= TOLERANCE:
                    name = known_names[best_match_index]
                    role = known_roles[best_match_index]

            status = ""

            with marked_lock:
                if name in already_marked:
                    status = "Already Marked"
                elif name != "Unknown":
                    status = mark_attendance(name, role)
                    if status != "Waiting for Course":
                        already_marked.add(name)
                        if name not in already_printed:
                            print(f"[{camera_name}] {name} | {status}")
                            already_printed.add(name)
            face_names.append(name)
            face_roles.append(role)
            face_statuses.append(status)

        # Display
        for (top, right, bottom, left), name, role, status in zip(
                face_locations, face_names, face_roles, face_statuses):
            top *= 4; right *= 4; bottom *= 4; left *= 4

            color = ROLE_COLORS.get(role, (0, 0, 255))
            label = f"{name} | {status}" if status else name

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 30), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, label, (left + 6, bottom - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        cv2.putText(frame, f"{camera_name} | {now_str}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow(window_name, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyWindow(window_name)
    print(f"[INFO] {camera_name} বন্ধ হয়েছে।")

# ==========================================
# Camera Setup
# ==========================================
print("=" * 50)
print("  Face Recognition Attendance System")
print("=" * 50)
print("\nকোন camera গুলো use করবেন?")
print("1. শুধু Laptop Webcam")
print("2. Laptop + Phone Camera")
print("3. Laptop + ESP32-CAM")
print("4. Laptop + Phone + ESP32-CAM (সব)")
print("5. শুধু Phone Camera")
print("6. শুধু ESP32-CAM")
print("=" * 50)

CAMERA_CODE = input("এই Camera এর Room number (যেমন 804): ").strip()

polling_thread = threading.Thread(target=poll_camera_command, daemon=True)
polling_thread.start()
print(f"[INFO] Camera Command Polling চালু হয়েছে (Room {CAMERA_CODE})। CR থেকে command এর অপেক্ষায়...\n")

choice = input("আপনার choice (1-6): ").strip()

cameras = []  # (source, name, window_name)

# Laptop webcam
if choice in ["1", "2", "3", "4"]:
    cameras.append((0, "Laptop Webcam", "Laptop Webcam"))

# Phone camera
if choice in ["2", "4", "5"]:
    ip = input("Phone এর IP address (যেমন 192.168.1.5): ").strip()
    port = input("Port (default 8080, Enter চাপুন): ").strip() or "8080"
    cameras.append((f"http://{ip}:{port}/video", "Phone Camera", "Phone Camera"))

# ESP32-CAM
if choice in ["3", "4", "6"]:
    ip = input("ESP32-CAM এর IP address (যেমন 192.168.1.6): ").strip()
    cameras.append((f"http://{ip}:81/stream", "ESP32-CAM", "ESP32-CAM"))

if not cameras:
    print("[ERROR] কোনো camera select করা হয়নি!")
    exit()

print(f"\n[INFO] মোট {len(cameras)} টি camera চালু হবে।")
print("[INFO] বন্ধ করতে যেকোনো window তে 'q' চাপুন।\n")

# ==========================================
# Sync offline data first
# ==========================================
sync_offline()

# ==========================================
# Start Threads
# ==========================================
threads = []
for source, name, window in cameras:
    t = threading.Thread(
        target=camera_thread,
        args=(source, name, window),
        daemon=True
    )
    threads.append(t)
    t.start()

# Wait for all threads
for t in threads:
    t.join()

cv2.destroyAllWindows()
print("[INFO] সব camera বন্ধ হয়েছে।")