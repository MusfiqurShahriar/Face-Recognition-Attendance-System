import cv2
import numpy as np
import face_recognition
import csv
import os

def compute_moire_score(gray):
    f_transform = np.fft.fft2(gray)
    f_shift = np.fft.fftshift(f_transform)
    magnitude = np.log(np.abs(f_shift) + 1)
    h, w = gray.shape
    cy, cx = h // 2, w // 2
    inner_r = min(h, w) // 8
    outer_r = min(h, w) // 2
    Y, X = np.ogrid[:h, :w]
    dist = np.sqrt((Y - cy) ** 2 + (X - cx) ** 2)
    ring_mask = (dist >= inner_r) & (dist <= outer_r)
    return magnitude[ring_mask].mean()

def compute_lbp_texture_score(gray):
    h, w = gray.shape
    if h < 16 or w < 16:
        return 0.0

    center = gray[1:-1, 1:-1].astype(np.int16)
    lbp = np.zeros_like(center, dtype=np.uint8)

    shifts = [(-1, -1), (-1, 0), (-1, 1), (0, 1),
              (1, 1), (1, 0), (1, -1), (0, -1)]
    for i, (dy, dx) in enumerate(shifts):
        neighbor = gray[1 + dy: h - 1 + dy, 1 + dx: w - 1 + dx].astype(np.int16)
        lbp |= ((neighbor >= center).astype(np.uint8)) << i
    hist, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256))
    hist = hist.astype(np.float32)
    hist /= (hist.sum() + 1e-6)

    entropy = -np.sum(hist * np.log2(hist + 1e-9))
    return entropy

def get_signals(face_img):
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (150, 150))

    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_mean = np.mean(np.sqrt(grad_x ** 2 + grad_y ** 2))

    moire_score = compute_moire_score(gray)
    texture_score = compute_lbp_texture_score(gray)

    return laplacian_var, gradient_mean, moire_score, texture_score

# Calibration Capture
CSV_FILE = "calibration_data.csv"
file_exists = os.path.exists(CSV_FILE)
csv_f = open(CSV_FILE, "a", newline="")
writer = csv.writer(csv_f)
if not file_exists:
    writer.writerow(["label", "laplacian", "gradient", "moire", "texture"])

print("=" * 55)
print(" Calibration Mode")
print(" 'r' চাপো -> এই মুহূর্তে face 'REAL' হিসেবে লগ হবে")
print(" 'f' চাপো -> এই মুহূর্তে face 'SPOOF (phone)' হিসেবে লগ হবে")
print(" 'q' চাপো -> বন্ধ করো")
print("=" * 55)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_small_frame)

    label_text = "কোনো face নেই"
    current_face_img = None

    if face_locations:
        top, right, bottom, left = [x * 4 for x in face_locations[0]]
        current_face_img = frame[top:bottom, left:right]
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        label_text = "Face detected - 'r' (real) / 'f' (spoof) চাপো"

    cv2.putText(frame, label_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.imshow("Calibration", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    elif key == ord('r') and current_face_img is not None and current_face_img.size > 0:
        lap, grad, moire, tex = get_signals(current_face_img)
        writer.writerow(["real", f"{lap:.2f}", f"{grad:.2f}", f"{moire:.3f}", f"{tex:.3f}"])
        csv_f.flush()
        print(f"[LOGGED - REAL]   Lap={lap:.1f} Grad={grad:.1f} Moire={moire:.2f} Tex={tex:.2f}")
    elif key == ord('f') and current_face_img is not None and current_face_img.size > 0:
        lap, grad, moire, tex = get_signals(current_face_img)
        writer.writerow(["spoof", f"{lap:.2f}", f"{grad:.2f}", f"{moire:.3f}", f"{tex:.3f}"])
        csv_f.flush()
        print(f"[LOGGED - SPOOF]  Lap={lap:.1f} Grad={grad:.1f} Moire={moire:.2f} Tex={tex:.2f}")

cap.release()
cv2.destroyAllWindows()
csv_f.close()
print(f"\n[INFO] ডেটা সেভ হয়েছে: {CSV_FILE}")