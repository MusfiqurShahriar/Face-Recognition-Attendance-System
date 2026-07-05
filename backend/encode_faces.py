import face_recognition
import os
import pickle
import numpy as np
from PIL import Image

DATASET_PATH = "../dataset"
ENCODINGS_FILE = "../models/encodings.pkl"

known_encodings = []
known_names = []
known_roles = []

print("[INFO] Dataset থেকে face encoding তৈরি হচ্ছে...")

for role in ["students", "teachers"]:
    role_path = os.path.join(DATASET_PATH, role)
    if not os.path.isdir(role_path):
        print(f"[WARNING] {role} ফোল্ডার পাওয়া যায়নি, skip")
        continue
    for person_name in os.listdir(role_path):
        person_folder = os.path.join(role_path, person_name)
        if not os.path.isdir(person_folder):
            continue
        for image_file in os.listdir(person_folder):
            image_path = os.path.join(person_folder, image_file)

            if not image_file.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            try:
                pil_image = Image.open(image_path).convert("RGB")
                rgb_image = np.array(pil_image, dtype=np.uint8)
            except Exception as e:
                print(f"[SKIP] {image_file} — {e}")
                continue

            face_locations = face_recognition.face_locations(rgb_image, number_of_times_to_upsample=2)

            if len(face_locations) == 0:
                print(f"[WARNING] {image_file} — মুখ পাওয়া যায়নি, skip")
                continue

            encodings = face_recognition.face_encodings(rgb_image, face_locations, num_jitters=2)

            known_encodings.append(encodings[0])
            known_names.append(person_name)
            known_roles.append(role)
            print(f"[OK] [{role}] {person_name} — {image_file}")

data = {
    "encodings": known_encodings,
    "names": known_names,
    "roles": known_roles
}
with open(ENCODINGS_FILE, "wb") as f:
    pickle.dump(data, f)
print(f"\n[DONE] মোট {len(known_names)} টি encoding সেভ হয়েছে → models/encodings.pkl")
print(f"  Students: {known_roles.count('students')}")
print(f"  Teachers: {known_roles.count('teachers')}")