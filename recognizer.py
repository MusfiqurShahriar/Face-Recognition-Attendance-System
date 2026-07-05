import cv2
import face_recognition
import os
import numpy as np

# ১. ডেটাসেট ফোল্ডার থেকে ছবিগুলো লোড করা
path = 'dataset'
known_face_encodings = []
known_face_names = []
print("ছবি লোড হচ্ছে এবং এনকোডিং তৈরি হচ্ছে... একটু অপেক্ষা করুন।")
# ফোল্ডারের ভেতরের সব ফোল্ডার ও ছবি পড়া
for person_name in os.listdir(path):
    person_folder = os.path.join(path, person_name)
    # এটি আসলেই একটি ফোল্ডার কিনা তা চেক করা
    if os.path.isdir(person_folder):
        for image_name in os.listdir(person_folder):
            image_path = os.path.join(person_folder, image_name)
            
            try:
                # ছবি লোড করা
                current_image = face_recognition.load_image_file(image_path)
                # এনকোডিং
                encodings = face_recognition.face_encodings(current_image)
                # যদি ছবিতে কোনো মুখ পাওয়া যায়
                if len(encodings) > 0:
                    known_face_encodings.append(encodings[0])
                    known_face_names.append(person_name)
            except Exception as e:
                print(f"Error loading {image_path}: {e}")
print("এনকোডিং শেষ! ক্যামেরা চালু হচ্ছে...")
# ২. ক্যামেরা চালু করা
video_capture = cv2.VideoCapture(0)
while True:
    ret, frame = video_capture.read()
    if not ret:
        print("ক্যামেরা থেকে সিগন্যাল পাওয়া যাচ্ছে না!")
        break
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
        # আসল ফ্রেমে বক্স আঁকার জন্য কোঅর্ডিনেট আবার ৪ গুণ বড় করা
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4
        # মুখের চারপাশে সবুজ চারকোনা বক্স আঁকা
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        # নিচে নাম লেখার জন্য ব্যাকগ্রাউন্ড
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)
    # ভিডিও স্ক্রিনে দেখানো
    cv2.imshow('Face Attendance System - Live Camera', frame)
    # কীবোর্ডের 'q' বাটন চাপলে ক্যামেরা বন্ধ হয়ে যাবে
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
video_capture.release()
cv2.destroyAllWindows()