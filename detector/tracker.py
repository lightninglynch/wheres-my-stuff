# detector/tracker.py
import cv2
import time
import requests
from ultralytics import YOLO
import math

API_ENDPOINT   = "https://<your-api-id>.execute-api.<region>.amazonaws.com/prod/track"
MODEL_PATH     = "yolov8n.pt"  # or your custom model
TARGET_CLASSES = {"wallet", "key", "charger", "cell phone"}
ALL_CLASSES    = TARGET_CLASSES.union({"lamp", "book", "bottle"})  # extend as you add more

def center(box):
    # box.xyxy = [x1, y1, x2, y2]
    x1, y1, x2, y2 = box.xyxy[0].tolist()
    return ((x1 + x2) / 2, (y1 + y2) / 2)

def main():
    model = YOLO(MODEL_PATH)
    cap   = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)[0]
        detections = []
        for b in results.boxes:
            cls_name = model.names[int(b.cls)]
            if cls_name in ALL_CLASSES:
                detections.append({
                    "class": cls_name,
                    "box": b,
                    "center": center(b)
                })

        # for each target, find neighbors
        for det in detections:
            obj = det["class"]
            if obj not in TARGET_CLASSES:
                continue

            cx, cy = det["center"]
            neighbors = []
            for other in detections:
                if other["class"] == obj:
                    continue
                ox, oy = other["center"]
                dist = math.hypot(ox - cx, oy - cy)
                if dist < 100:  # within 100px
                    neighbors.append(other["class"])
            neighbors = list(sorted(set(neighbors)))

            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            payload = {
                "object": obj,
                "timestamp": ts,
                "neighbors": neighbors
            }
            try:
                r = requests.post(API_ENDPOINT, json=payload, timeout=2)
                r.raise_for_status()
            except Exception as e:
                print("⚠️  Failed to send:", e)

        cv2.imshow("Object Finder", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
