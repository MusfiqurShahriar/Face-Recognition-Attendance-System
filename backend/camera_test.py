import cv2

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("[ERROR] ক্যামেরা খুলতে পারছে না!")
    exit()
print("[INFO] ক্যামেরা চালু হয়েছে। বন্ধ করতে 'q' চাপো।")
while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] ফ্রেম পড়তে পারছে না!")
        break
    cv2.imshow("Camera Test", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()