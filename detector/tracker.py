"""Webcam detector: YOLO-World finds household items and posts last-seen locations."""

from __future__ import annotations

import logging
import math
import os
import sys
import time
from pathlib import Path

import cv2
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.names import (  # noqa: E402
    CANONICAL_OBJECTS,
    LANDMARKS,
    canonicalize,
    parse_class_list,
    yolo_prompts,
)

load_dotenv(ROOT / "detector" / ".env")
load_dotenv()

log = logging.getLogger("tracker")

NEIGHBOR_PIXELS_DEFAULT = 150
DEBOUNCE_SECONDS_DEFAULT = 20
CONFIDENCE_DEFAULT = 0.3


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        log.warning("Invalid %s=%r; using %s", name, raw, default)
        return default


def _env_int(name: str, default: int) -> int:
    return int(_env_float(name, default))


def _load_model(model_path: str, prompts: list[str]):
    try:
        from ultralytics import YOLOWorld

        model = YOLOWorld(model_path)
    except Exception:
        from ultralytics import YOLO

        model = YOLO(model_path)
    model.set_classes(prompts)
    return model


def _box_center(box) -> tuple[float, float]:
    x1, y1, x2, y2 = box.xyxy[0].tolist()
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def _draw_box(frame, box, label: str, tracked: bool) -> None:
    x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
    color = (40, 180, 40) if tracked else (160, 160, 160)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    text_y = y1 - 8 if y1 > 20 else y1 + 18
    cv2.putText(
        frame,
        label,
        (x1, text_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        color,
        2,
        cv2.LINE_AA,
    )


def _should_send(
    last_sent: dict[str, tuple[float, tuple[str, ...]]],
    obj: str,
    neighbors: tuple[str, ...],
    now: float,
    debounce_seconds: float,
) -> bool:
    prev = last_sent.get(obj)
    if prev is None:
        return True
    prev_time, prev_neighbors = prev
    if neighbors != prev_neighbors:
        return True
    return (now - prev_time) >= debounce_seconds


def _post_location(
    endpoint: str,
    api_key: str,
    payload: dict,
) -> None:
    if not endpoint:
        log.info("No API_ENDPOINT set; would send %s", payload)
        return
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    response = requests.post(endpoint, json=payload, headers=headers, timeout=5)
    response.raise_for_status()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    endpoint = os.environ.get("API_ENDPOINT", "").strip()
    api_key = os.environ.get("API_KEY", "").strip()
    camera_index = _env_int("CAMERA_INDEX", 0)
    confidence = _env_float("CONFIDENCE", CONFIDENCE_DEFAULT)
    debounce_seconds = _env_float("DEBOUNCE_SECONDS", DEBOUNCE_SECONDS_DEFAULT)
    neighbor_pixels = _env_float("NEIGHBOR_PIXELS", NEIGHBOR_PIXELS_DEFAULT)
    model_path = os.environ.get("MODEL_PATH", "yolov8s-worldv2.pt").strip()

    tracked = parse_class_list(os.environ.get("TRACKED_OBJECTS"), CANONICAL_OBJECTS)
    landmarks = parse_class_list(os.environ.get("LANDMARKS"), LANDMARKS)
    tracked_set = set(tracked)
    prompts = yolo_prompts(tracked, landmarks)

    log.info("Loading %s with classes: %s", model_path, ", ".join(prompts))
    model = _load_model(model_path, prompts)
    names = model.names

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        log.error("Could not open camera index %s", camera_index)
        return 1

    last_sent: dict[str, tuple[float, tuple[str, ...]]] = {}
    log.info("Detector running. Press q in the video window to quit.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                log.error("Camera frame read failed")
                break

            results = model.predict(frame, verbose=False)[0]
            detections = []
            for box in results.boxes:
                conf = float(box.conf[0]) if box.conf is not None else 0.0
                if conf < confidence:
                    continue
                cls_id = int(box.cls[0])
                raw_name = names.get(cls_id, str(cls_id)) if isinstance(names, dict) else names[cls_id]
                canonical = canonicalize(raw_name)
                if not canonical:
                    continue
                detections.append(
                    {
                        "class": canonical,
                        "box": box,
                        "center": _box_center(box),
                        "conf": conf,
                    }
                )
                _draw_box(
                    frame,
                    box,
                    f"{canonical} {conf:.2f}",
                    canonical in tracked_set,
                )

            now = time.time()
            seen_targets = set()
            for det in detections:
                obj = det["class"]
                if obj not in tracked_set or obj in seen_targets:
                    continue
                seen_targets.add(obj)

                cx, cy = det["center"]
                neighbors = []
                for other in detections:
                    if other["class"] == obj:
                        continue
                    ox, oy = other["center"]
                    if math.hypot(ox - cx, oy - cy) < neighbor_pixels:
                        neighbors.append(other["class"])
                neighbor_tuple = tuple(sorted(set(neighbors)))

                if not _should_send(last_sent, obj, neighbor_tuple, now, debounce_seconds):
                    continue

                payload = {
                    "object": obj,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "neighbors": list(neighbor_tuple),
                }
                try:
                    _post_location(endpoint, api_key, payload)
                    last_sent[obj] = (now, neighbor_tuple)
                    log.info("Posted %s near %s", obj, neighbor_tuple or "nothing")
                except Exception as exc:
                    log.warning("Failed to send %s: %s", obj, exc)

            cv2.imshow("Object Finder", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
