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
from collections import deque, defaultdict

ENCODINGS_FILE = "../models/encodings.pkl"
OFFLINE_FILE = "offline_queue.json"

TOLERANCE = 0.45
CURRENT_SEMESTER = None

from dotenv import load_dotenv
load_dotenv()

BASE_URL = os.getenv("SERVER_BASE_URL", "https://face-recognition-attendance-system-yuhz.onrender.com")
SERVER_URL = f"{BASE_URL}/api/mark-attendance"
POLL_URL = f"{BASE_URL}/api/camera-command"
HEARTBEAT_URL = f"{BASE_URL}/api/camera-heartbeat"

HEARTBEAT_INTERVAL_SECONDS = 20

# ==========================================
# Room Camera Config — ক্যামেরা কেনার পর এখানে IP বসাও
# ==========================================
ROOM_CAMERA_URLS = {
    "804": 0,
    "805": "rtsp://admin:password@192.168.0.102:554/stream1",
    "806": "rtsp://admin:password@192.168.0.103:554/stream1",
    "807": "rtsp://admin:password@192.168.0.104:554/stream1",
}

# ==========================================
# Shared State (Thread-safe)
# ==========================================
already_marked = {}
already_printed = {}
marked_lock = threading.Lock()

# room_states এখন শুধু course/session info না, camera on/off (enabled) state-ও রাখবে
room_states = {}
room_states_lock = threading.Lock()

def _init_room_state(room_code):
    room_states[room_code] = {
        "course_id": None,
        "session_id": None,
        "course_code": None,
        "enabled": False,   # dashboard থেকে on/off — শুরুতে False, প্রথম poll এ ঠিক হবে
    }

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
# Blur Detection (Laplacian Variance)
# ==========================================
BLUR_VARIANCE_THRESHOLD = 60.0

def _is_face_sharp_enough(face_crop_bgr):
    if face_crop_bgr is None or face_crop_bgr.size == 0:
        return False
    gray = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance >= BLUR_VARIANCE_THRESHOLD

# ==========================================
# Blink-based Liveness Detection
# ==========================================
EAR_THRESHOLD = 0.21
EAR_CONSEC_FRAMES = 2
EAR_MAX_LOW_FRAMES = 8
EAR_SMOOTHING_WINDOW = 4
LIVENESS_TIMEOUT_SECONDS = 8

liveness_state = defaultdict(lambda: {
    "ear_history": deque(maxlen=EAR_SMOOTHING_WINDOW),
    "consec_low": 0,
    "blinked": False,
    "first_seen": time.time(),
    "last_seen": time.time(),
    "landmark_fail_count": 0,
})
liveness_lock = threading.Lock()

def _eye_aspect_ratio(eye_points):
    p = [np.array(pt) for pt in eye_points]
    A = np.linalg.norm(p[1] - p[5])
    B = np.linalg.norm(p[2] - p[4])
    C = np.linalg.norm(p[0] - p[3])
    return (A + B) / (2.0 * C) if C != 0 else 0.0

def _get_landmarks_robust(rgb_frame, face_location_full_res):
    top, right, bottom, left = face_location_full_res
    h, w = rgb_frame.shape[:2]

    pad_y = int((bottom - top) * 0.25)
    pad_x = int((right - left) * 0.25)

    crop_top = max(0, top - pad_y)
    crop_left = max(0, left - pad_x)
    crop_bottom = min(h, bottom + pad_y)
    crop_right = min(w, right + pad_x)

    crop = rgb_frame[crop_top:crop_bottom, crop_left:crop_right]
    if crop.size == 0:
        return []

    rel_top = top - crop_top
    rel_left = left - crop_left
    rel_bottom = rel_top + (bottom - top)
    rel_right = rel_left + (right - left)

    try:
        landmarks_list = face_recognition.face_landmarks(
            crop, face_locations=[(rel_top, rel_right, rel_bottom, rel_left)]
        )
    except Exception:
        landmarks_list = []

    return landmarks_list

def _update_liveness(name, rgb_frame, bgr_face_crop, face_location_full_res):
    if not _is_face_sharp_enough(bgr_face_crop):
        return False, "Image too blurry, hold steady"

    landmarks_list = _get_landmarks_robust(rgb_frame, face_location_full_res)

    with liveness_lock:
        state = liveness_state[name]
        now = time.time()
        state["last_seen"] = now

        if not state["blinked"] and (now - state["first_seen"]) > LIVENESS_TIMEOUT_SECONDS:
            state["first_seen"] = now
            state["consec_low"] = 0
            state["ear_history"].clear()

        if state["blinked"]:
            return True, "Verified (Live)"

        if not landmarks_list or "left_eye" not in landmarks_list[0]:
            state["landmark_fail_count"] += 1
            return False, "Verifying liveness..."

        state["landmark_fail_count"] = 0
        landmarks = landmarks_list[0]
        raw_ear = (_eye_aspect_ratio(landmarks["left_eye"]) + _eye_aspect_ratio(landmarks["right_eye"])) / 2.0

        state["ear_history"].append(raw_ear)
        smoothed_ear = float(np.median(state["ear_history"]))

        if smoothed_ear < EAR_THRESHOLD:
            state["consec_low"] += 1
            if state["consec_low"] > EAR_MAX_LOW_FRAMES:
                state["consec_low"] = EAR_MAX_LOW_FRAMES + 1
        else:
            if EAR_CONSEC_FRAMES <= state["consec_low"] <= EAR_MAX_LOW_FRAMES:
                state["blinked"] = True
                return True, "Verified (Live)"
            state["consec_low"] = 0

        return False, "Verifying liveness..."

def _cleanup_stale_liveness():
    with liveness_lock:
        for n in [n for n, s in liveness_state.items() if time.time() - s["last_seen"] > 30]:
            del liveness_state[n]

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

# ==========================================
# Attendance Marking (room-aware)
# ==========================================
def mark_attendance(name, role, room_code):
    with room_states_lock:
        state = room_states.get(room_code, {})
        course_id = state.get("course_id")
        session_id = state.get("session_id")

    if course_id is None:
        return "Waiting for Course"

    payload = {
        "name": name,
        "role": role.rstrip("s"),
        "semester": CURRENT_SEMESTER,
        "course_id": course_id,
        "session_id": session_id
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

# ==========================================
# Camera Command + On/Off Polling (per room)
# ==========================================
def poll_camera_command(room_code):
    """
    প্রতি ৫ সেকেন্ডে একবার সার্ভারকে জিজ্ঞেস করে:
    - এই room camera dashboard থেকে on/off করা আছে কিনা (status == "disabled" হলে off)
    - কোন course/session এখন active
    """
    first_poll_done = False
    while True:
        try:
            res = requests.get(f"{POLL_URL}/{room_code}", timeout=5)
            if res.status_code == 200:
                data = res.json()
                status = data.get("status")

                if status == "disabled":
                    # dashboard থেকে বন্ধ করা আছে
                    with room_states_lock:
                        room_states[room_code]["enabled"] = False
                        room_states[room_code]["course_id"] = None
                        room_states[room_code]["session_id"] = None
                    time.sleep(5)
                    continue

                # disabled না, মানে camera-টা enabled আছে dashboard থেকে
                with room_states_lock:
                    was_enabled = room_states[room_code]["enabled"]
                    room_states[room_code]["enabled"] = True
                    if not was_enabled:
                        print(f"\n[COMMAND][Room {room_code}] Dashboard থেকে Camera ON করা হলো।\n")

                if status == "success":
                    if not first_poll_done:
                        first_poll_done = True
                        time.sleep(5)
                        continue

                    new_course = data.get("course_id")
                    with room_states_lock:
                        current = room_states[room_code]["course_id"]
                        if new_course != current:
                            room_states[room_code]["course_id"] = new_course
                            room_states[room_code]["session_id"] = data.get("session_id")
                            room_states[room_code]["course_code"] = data.get("course_code")

                            if new_course is None:
                                print(f"\n[COMMAND][Room {room_code}] Attendance বন্ধ করা হলো, Waiting for Course...\n")
                                with marked_lock:
                                    already_marked[room_code] = set()
                                    already_printed[room_code] = set()
                            else:
                                print(f"\n[COMMAND][Room {room_code}] নতুন Course activate হলো: {data.get('course_code')} (course_id={new_course})\n")
                # status == "no_command" হলে শুধু enabled=True থেকে যাবে, course_id None-ই থাকবে (Waiting for Course দেখাবে)
        except requests.exceptions.RequestException:
            pass
        time.sleep(5)

def _maybe_send_heartbeat(room_code, last_sent_tracker):
    """
    শুধুমাত্র camera আসলে video capture করছে (frame আসছে) তখনই heartbeat পাঠানো
    হবে — এতে dashboard-এ "Active" মানে সত্যিই সেই camera চলছে, শুধু script
    চালু আছে এটা না। last_sent_tracker একটা dict, প্রতি room এর শেষ পাঠানোর
    সময় মনে রাখে যাতে প্রতি frame এ না পাঠিয়ে ইন্টারভাল মেনে চলে।
    """
    now = time.time()
    last_sent = last_sent_tracker.get(room_code, 0)
    if now - last_sent >= HEARTBEAT_INTERVAL_SECONDS:
        last_sent_tracker[room_code] = now
        try:
            requests.post(f"{HEARTBEAT_URL}/{room_code}", timeout=5)
        except requests.exceptions.RequestException:
            pass

_heartbeat_last_sent = {}

# ==========================================
# Camera Thread (room-aware, resilient, on/off controllable)
# ==========================================
def camera_thread(camera_source, camera_name, window_name, room_code):
    print(f"[INFO] {camera_name} thread প্রস্তুত। Dashboard থেকে ON করার অপেক্ষায়...")
    with marked_lock:
        if room_code not in already_marked:
            already_marked[room_code] = set()
        if room_code not in already_printed:
            already_printed[room_code] = set()

    cap = None
    window_open = False
    fail_count = 0

    while True:
        with room_states_lock:
            is_enabled = room_states[room_code]["enabled"]

        # ==== Camera OFF থাকলে: capture বন্ধ, window বন্ধ, শুধু wait করবে ====
        if not is_enabled:
            if cap is not None:
                cap.release()
                cap = None
            if window_open:
                cv2.destroyWindow(window_name)
                window_open = False
            time.sleep(2)
            continue

        # ==== Camera ON, কিন্তু এখনো capture শুরু হয়নি — শুরু করো ====
        if cap is None:
            print(f"[INFO] {camera_name} চালু হচ্ছে...")
            cap = cv2.VideoCapture(camera_source)
            fail_count = 0
            if not cap.isOpened():
                print(f"[ERROR] {camera_name} খুলতে পারেনি! ৫ সেকেন্ড পর আবার চেষ্টা হবে।")
                cap = None
                time.sleep(5)
                continue
            print(f"[OK] {camera_name} চালু হয়েছে।")
            window_open = True

        ret, frame = cap.read()
        _cleanup_stale_liveness()
        if ret:
            # সফলভাবে frame পাওয়া গেছে — মানে camera সত্যিকারভাবে সচল, heartbeat পাঠাও
            _maybe_send_heartbeat(room_code, _heartbeat_last_sent)
        if not ret:
            fail_count += 1
            print(f"[WARNING] {camera_name} থেকে frame পাওয়া যাচ্ছে না! (fail={fail_count})")
            if fail_count >= 10:
                print(f"[ERROR] {camera_name} বারবার fail করছে, reconnect চেষ্টা হবে।")
                cap.release()
                cap = None
                if window_open:
                    cv2.destroyWindow(window_name)
                    window_open = False
                time.sleep(3)
            else:
                time.sleep(1)
            continue
        fail_count = 0

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        face_roles = []
        face_statuses = []

        for face_encoding, face_location in zip(face_encodings, face_locations):
            top, right, bottom, left = [x * 4 for x in face_location]
            bgr_face_crop = frame[top:bottom, left:right]

            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=TOLERANCE)
            name = "Unknown"
            role = "Unknown"
            face_distances = face_recognition.face_distance(known_encodings, face_encoding)

            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index] and face_distances[best_match_index] <= TOLERANCE:
                    name = known_names[best_match_index]
                    role = known_roles[best_match_index]

            status = ""

            if name != "Unknown":
                rgb_full_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                is_live, liveness_status = _update_liveness(name, rgb_full_frame, bgr_face_crop, (top, right, bottom, left))

                with marked_lock:
                    if name in already_marked[room_code]:
                        status = "Already Marked"
                    elif not is_live:
                        status = liveness_status
                    else:
                        status = mark_attendance(name, role, room_code)
                        if status != "Waiting for Course":
                            already_marked[room_code].add(name)
                            if name not in already_printed[room_code]:
                                print(f"[{camera_name}] {name} | {status}")
                                already_printed[room_code].add(name)

            face_names.append(name)
            face_roles.append(role)
            face_statuses.append(status)

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
        cv2.waitKey(1)  # 'q' দিয়ে বন্ধ করার প্রয়োজন নেই — dashboard থেকেই control হবে

# ==========================================
# Setup — সব room camera automatically শুরু হবে
# (কোনো manual input লাগবে না, dashboard থেকে on/off নিয়ন্ত্রিত হবে)
# ==========================================
print("=" * 50)
print("  Face Recognition Attendance System")
print("  সব Room Camera Client চালু হচ্ছে (Auto Mode)")
print("=" * 50)

for room_code in ROOM_CAMERA_URLS.keys():
    _init_room_state(room_code)

print(f"[INFO] মোট {len(ROOM_CAMERA_URLS)} টি room camera thread প্রস্তুত হচ্ছে।")
print("[INFO] প্রতিটা camera admin dashboard থেকে ON করার পরই ভিডিও দেখাবে।\n")

# ==========================================
# Start Command Polling Threads (per room)
# Heartbeat আলাদা thread হিসেবে না, camera_thread এর ভিতর থেকেই পাঠানো হয়
# (শুধু camera সত্যিকারভাবে video capture করলেই heartbeat যাবে)
# ==========================================
for room_code in ROOM_CAMERA_URLS.keys():
    t1 = threading.Thread(target=poll_camera_command, args=(room_code,), daemon=True)
    t1.start()
    print(f"[INFO] Room {room_code}: Command Polling চালু হয়েছে।")

# ==========================================
# Sync offline data first
# ==========================================
sync_offline()

# ==========================================
# Start Camera Threads (সব room automatically)
# ==========================================
threads = []
for room_code, url in ROOM_CAMERA_URLS.items():
    t = threading.Thread(
        target=camera_thread,
        args=(url, f"Room {room_code} Camera", f"Room {room_code}", room_code),
        daemon=True
    )
    threads.append(t)
    t.start()
    time.sleep(1)

print("\n[INFO] সব camera thread চালু হয়েছে। এই terminal window বন্ধ করলে সব camera বন্ধ হয়ে যাবে —")
print("[INFO] তাই এটা background এ চালু রাখো (Task Scheduler/Startup দিয়ে auto-run করানোই ভালো)।\n")

for t in threads:
    t.join()

cv2.destroyAllWindows()
print("[INFO] সব camera বন্ধ হয়েছে।")