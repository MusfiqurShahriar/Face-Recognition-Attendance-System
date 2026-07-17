import cv2
import numpy as np
import onnxruntime as ort
import os
import urllib.request

MODEL_PATH = "../models/anti_spoof.onnx"
MODEL_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"

def download_model():
    if not os.path.exists(MODEL_PATH):
        print("[INFO] Anti-spoof model download হচ্ছে...")
        os.makedirs("../models", exist_ok=True)
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("[OK] Model download সম্পন্ন")

def is_real_face(face_img):
    """
    face_img: BGR format এ cropped face image
    Returns: True if real face, False if spoof
    """
    try:
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        h, w = gray.shape
        if h < 10 or w < 10:
            return True 
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude = 20 * np.log(np.abs(f_shift) + 1)
        freq_mean = np.mean(magnitude)
        if laplacian_var < 50:
            return False
        return True
    except Exception as e:
        print(f"[WARNING] Anti-spoof check failed: {e}")
        return True