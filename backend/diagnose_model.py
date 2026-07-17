import onnxruntime as ort
import numpy as np

MODEL_PATH = "../models/anti_spoof_model.onnx"

session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])

print("=" * 60)
print("INPUTS:")
for inp in session.get_inputs():
    print(f"  name={inp.name}  shape={inp.shape}  type={inp.type}")

print("\nOUTPUTS:")
for out in session.get_outputs():
    print(f"  name={out.name}  shape={out.shape}  type={out.type}")
print("=" * 60)

random_input = np.random.rand(1, 3, 80, 80).astype(np.float32)
input_name = session.get_inputs()[0].name
outputs = session.run(None, {input_name: random_input})
print(f"\n[TEST 1] সম্পূর্ণ Random noise input দিয়ে output:")
for i, o in enumerate(outputs):
    print(f"  output[{i}] shape={o.shape}  values={o}")

# একটা সম্পূর্ণ কালো (black) ছবি দিয়ে টেস্ট
black_input = np.zeros((1, 3, 80, 80), dtype=np.float32)
outputs2 = session.run(None, {input_name: black_input})
print(f"\n[TEST 2] সম্পূর্ণ কালো (all zero) input দিয়ে output:")
for i, o in enumerate(outputs2):
    print(f"  output[{i}] shape={o.shape}  values={o}")

# একটা সম্পূর্ণ সাদা (white) ছবি দিয়ে টেস্ট
white_input = np.ones((1, 3, 80, 80), dtype=np.float32)
outputs3 = session.run(None, {input_name: white_input})
print(f"\n[TEST 3] সম্পূর্ণ সাদা (all one) input দিয়ে output:")
for i, o in enumerate(outputs3):
    print(f"  output[{i}] shape={o.shape}  values={o}")