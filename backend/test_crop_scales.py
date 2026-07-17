"""
এই script আগে সেভ করা debug_full_crop.jpg (2.7x scale crop) ব্যবহার করে,
বিভিন্ন tightness/crop-level এ model output কেমন আসে সেটা টেস্ট করে।

উদ্দেশ্য: bounding box convention mismatch (dlib vs RetinaFace) আসলেই সমস্যা কিনা যাচাই করা।

চালানোর নিয়ম:
    python test_crop_scales.py debug_full_crop.jpg
"""
import sys
import cv2
import numpy as np
import onnxruntime as ort

MODEL_PATH = "../models/anti_spoof_model.onnx"

def run_model(session, input_name, img_80x80_bgr):
    input_tensor = img_80x80_bgr.astype(np.float32) / 255.0
    input_tensor = np.transpose(input_tensor, (2, 0, 1))
    input_tensor = np.expand_dims(input_tensor, axis=0)
    outputs = session.run(None, {input_name: input_tensor})
    logits = outputs[0][0]
    exp_logits = np.exp(logits - np.max(logits))
    probs = exp_logits / exp_logits.sum()
    label_idx = int(np.argmax(probs))
    return logits, probs, label_idx

def center_subcrop(img, fraction):
    """
    img এর কেন্দ্র থেকে fraction (0-1) অনুপাতে একটা tighter sub-crop নেয়।
    fraction=1.0 মানে পুরো ছবিটাই (কোনো পরিবর্তন নেই)।
    fraction=0.5 মানে কেন্দ্রের অর্ধেক অংশ (tighter crop, যেন কম margin/context সহ face)।
    """
    h, w = img.shape[:2]
    new_h, new_w = int(h * fraction), int(w * fraction)
    top = (h - new_h) // 2
    left = (w - new_w) // 2
    return img[top:top + new_h, left:left + new_w]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ব্যবহার: python test_crop_scales.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    full_crop = cv2.imread(image_path)
    if full_crop is None:
        print(f"[ERROR] ছবি পড়া যায়নি: {image_path}")
        sys.exit(1)

    session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name

    print(f"[INFO] মূল crop shape: {full_crop.shape}\n")

    # বিভিন্ন tightness টেস্ট করা হচ্ছে — 1.0 (বর্তমান, পুরো 2.7x crop),
    # 0.7, 0.5, 0.37 (এটা মোটামুটি 2.7x থেকে ~1.0x scale এর সমতুল্য একটা tighter crop)
    fractions = [1.0, 0.85, 0.7, 0.55, 0.37]

    for frac in fractions:
        sub = center_subcrop(full_crop, frac)
        resized = cv2.resize(sub, (80, 80))
        logits, probs, label_idx = run_model(session, input_name, resized)
        print(f"[fraction={frac:.2f}] sub_shape={sub.shape}  label_idx={label_idx}  probs={probs}")