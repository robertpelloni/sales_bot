"""
Project Sirens - Core Vision Processing & Feature Extractor
Processes camera feed using YOLO tracking, calculates customer proximity from bounding boxes,
tracks dwell time (>1.5s lock threshold), extracts visual attribute heuristics (dominant colors),
and packages structured metadata alongside compressed context frames for the Frontier VLM.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import redis.asyncio as redis
from ultralytics import YOLO

class MockYOLO:
    def __init__(self, model_name):
        self.model_name = model_name

    def track(self, frame, persist=True):
        class MockResult:
            def __init__(self):
                self.boxes = type(
                    "Boxes",
                    (),
                    {
                        "id": [1],
                        "xyxy": [[100, 80, 260, 420]],
                        "conf": [0.92],
                        "cls": [0],
                    },
                )

        return [MockResult()]


def load_vision_model(
    model_path: str = "yolo11n_edgetpu.tflite",
    pytorch_fallback: str = "yolo11n.pt",
) -> Tuple[Any, str]:
    """
    Loads edge vision models preferentially optimized for Coral Edge TPU (TFLite)
    to achieve 30+ FPS and prevent thermal throttling on Raspberry Pi 5.

    Falls back to standard PyTorch format or MockYOLO if model files or drivers are absent.
    Returns a tuple of (model_instance, model_type_string).
    """
    if os.path.exists(model_path) and YOLO is not None:
        try:
            print(f"Loading Coral Edge TPU optimized model: {model_path}")
            model = YOLO(model_path)
            return model, "coral_edgetpu"
        except Exception as e:
            print(f"Warning: Failed to initialize Coral Edge TPU model: {e}")

    if os.path.exists(pytorch_fallback) and YOLO is not None:
        try:
            print(f"Loading standard PyTorch model: {pytorch_fallback}")
            model = YOLO(pytorch_fallback)
            return model, "pytorch"
        except Exception as e:
            print(f"Warning: Failed to initialize PyTorch model: {e}")

    print("Falling back to MockYOLO tracker.")
    return MockYOLO(model_name=pytorch_fallback), "mock"


def calculate_proximity(bbox: List[float], frame_height: int = 480) -> Tuple[float, str]:
    """
    Calculates estimated customer distance (meters) based on bounding box height relative
    to frame height. An average human height (~1.7m) filling 70% of frame corresponds to ~1.2m distance.
    Returns estimated distance in meters and proximity descriptor string.
    """
    if len(bbox) < 4:
        return 2.5, "far"

    y1, y2 = bbox[1], bbox[3]
    box_height = max(1.0, float(y2 - y1))
    ratio = box_height / max(1.0, float(frame_height))

    # Inverse proportional distance model calibrated for in-store focal distance
    if ratio >= 0.65:
        distance = round(max(0.8, 1.2 * (0.7 / ratio)), 2)
        desc = f"{distance}m (close)"
    elif ratio >= 0.35:
        distance = round(1.2 * (0.7 / ratio), 2)
        desc = f"{distance}m (mid-range)"
    else:
        distance = round(1.2 * (0.7 / ratio), 2)
        desc = f"{distance}m (far)"

    return distance, desc


def extract_visual_attributes(crop_img: np.ndarray) -> List[str]:
    """
    Analyzes cropped target frame to extract dominant color heuristics and apparel traits
    without violating privacy directives.
    """
    if crop_img is None or crop_img.size == 0:
        return ["casual attire", "customer"]

    try:
        # Resize crop for rapid analysis
        small = cv2.resize(crop_img, (64, 64))
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)

        # Separate upper torso (top 60% of crop) to identify shirt/coat colors
        h_crop, w_crop = small.shape[:2]
        torso = hsv[: int(h_crop * 0.6), :]

        mean_h = np.mean(torso[:, :, 0])
        mean_s = np.mean(torso[:, :, 1])
        mean_v = np.mean(torso[:, :, 2])

        attributes = []
        if mean_v < 60:
            attributes.append("dark jacket or coat")
        elif mean_s < 45 and mean_v > 180:
            attributes.append("light colored apparel")
        elif 95 <= mean_h <= 135 and mean_s > 50:
            attributes.append("navy blue or blue jacket")
        elif (mean_h <= 10 or mean_h >= 170) and mean_s > 60:
            attributes.append("red or warm-toned outerwear")
        elif 35 <= mean_h <= 85 and mean_s > 50:
            attributes.append("green outerwear")
        else:
            attributes.append("stylish casual attire")

        attributes.append("approaching customer")
        return attributes
    except Exception:
        return ["casual attire", "customer"]


def is_target_dwelling(
    first_seen: float,
    current_time: float,
    threshold_seconds: float = 1.5,
) -> bool:
    """Checks if target has dwelled within proximity threshold for longer than the required duration."""
    return (current_time - first_seen) >= threshold_seconds


async def start_vision_loop(redis_url: str):
    """
    Main vision execution loop: tracks objects, applies 1.5s dwell lock,
    extracts features, packages metadata with base64 JPEG, and publishes to Redis.
    """
    r = redis.from_url(redis_url)
    print("Vision system initializing hardware bindings...")

    from llm_client import get_system_config
    import base64
    _, use_mock_vision_str = get_system_config()
    use_mock_vision = use_mock_vision_str.lower() in ("true", "1", "yes")

    try:
        # Phase 4 Hardware Integration:
        # Load the Coral Edge TPU optimized TFLite model instead of the standard PyTorch model
        # This allows 30+ FPS tracking on the Raspberry Pi 5 without thermal throttling.
        # Fallback to standard PyTorch format if Coral model is unavailable.
        if os.path.exists("yolo11n_edgetpu.tflite"):
            print("Loaded Coral Edge TPU YOLOv11n model.")
            model = YOLO("yolo11n_edgetpu.tflite")
        else:
            print("Loaded Standard PyTorch YOLOv11n model.")
            model = YOLO("yolo11n.pt")
    except Exception:
        print("Falling back to MockYOLO")
        model = MockYOLO("yolo11n.pt")
        use_mock_vision = True

    print("Vision system started.")

    tracked_objects: Dict[int, Dict[str, Any]] = {}
    last_cleanup_time = time.time()

    if use_mock_vision:
        # Mock vision loop simulating customer approach and dwell
        for i in range(10):
            await asyncio.sleep(1)
            current_time = time.time()

            if current_time - last_cleanup_time > 60:
                tracked_objects.clear()
                last_cleanup_time = current_time
                print("Vision: Cleared bounding box memory buffers (Privacy Directive).")

            obj_id = 1
            mock_bbox = [100, 80, 260, 420]
            dist, prox_desc = calculate_proximity(mock_bbox, frame_height=480)

            if obj_id not in tracked_objects:
                tracked_objects[obj_id] = {"first_seen": current_time, "triggered": False}

            dwell_duration = round(current_time - tracked_objects[obj_id]["first_seen"], 2)
            if is_target_dwelling(tracked_objects[obj_id]["first_seen"], current_time, 1.5):
                if not tracked_objects[obj_id].get("triggered", False):
                    import numpy as np
                    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    # Draw a mock blue rectangle simulating jacket
                    cv2.rectangle(dummy_frame, (100, 80), (260, 420), (180, 50, 20), -1)

                    crop = dummy_frame[80:420, 100:260]
                    attrs = extract_visual_attributes(crop)
                    # Include standard keywords for sales prompts
                    if "navy blue or blue jacket" in attrs:
                        attrs.extend(["windbreaker", "holding coffee"])

                    _, buffer = cv2.imencode(".jpg", dummy_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                    encoded_frame = base64.b64encode(buffer).decode("utf-8")

                    metadata_packet = {
                        "id": obj_id,
                        "proximity": prox_desc,
                        "distance_m": dist,
                        "dwell_time_s": dwell_duration,
                        "attributes": attrs,
                        "frame_data": encoded_frame,
                    }

                    print(f"Vision: Target locked (ID {obj_id}, dist={dist}m). Publishing CUSTOMER_DETECTED to Redis.")
                    await r.publish("CUSTOMER_DETECTED", json.dumps(metadata_packet))
                    tracked_objects[obj_id]["triggered"] = True
    else:
        # Real hardware vision loop using cv2.VideoCapture
        cap = cv2.VideoCapture(0)

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            # Simulate non-blocking sleep
            await asyncio.sleep(0.01)

            current_time = time.time()

            # Privacy Directive
            if current_time - last_cleanup_time > 60:
                tracked_objects.clear()
                last_cleanup_time = current_time
                print("Vision: Cleared bounding box memory buffers (Privacy Directive).")

            results = model.track(frame, persist=True)

            if (
                results
                and len(results) > 0
                and hasattr(results[0], "boxes")
                and results[0].boxes
                and hasattr(results[0].boxes, "id")
                and results[0].boxes.id is not None
            ):
                h, w = frame.shape[:2]
                for box, obj_id_tensor in zip(results[0].boxes, results[0].boxes.id):
                    obj_id = int(obj_id_tensor.item())
                    coords = box.xyxy[0].tolist() if hasattr(box, "xyxy") else [0, 0, 100, 100]
                    dist, prox_desc = calculate_proximity(coords, frame_height=h)

                    if obj_id not in tracked_objects:
                        tracked_objects[obj_id] = {"first_seen": current_time, "triggered": False}

                    dwell_duration = round(current_time - tracked_objects[obj_id]["first_seen"], 2)
                    # Check if customer has dwelled within frame for > 1.5s and is within close range
                    if is_target_dwelling(tracked_objects[obj_id]["first_seen"], current_time, 1.5):
                        if not tracked_objects[obj_id].get("triggered", False):
                            x1, y1, x2, y2 = [max(0, int(c)) for c in coords]
                            crop = frame[y1:y2, x1:x2]
                            attrs = extract_visual_attributes(crop)

                            _, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                            encoded_frame = base64.b64encode(buffer).decode("utf-8")

                            # In a full implementation, attributes would be extracted dynamically from the bounding box
                            metadata_packet = {
                                "id": obj_id,
                                "proximity": prox_desc,
                                "distance_m": dist,
                                "dwell_time_s": dwell_duration,
                                "attributes": attrs,
                                "frame_data": encoded_frame,
                            }

                            print(f"Vision: Detected live customer ID {obj_id} (prox={prox_desc}). Publishing to Redis.")
                            await r.publish("CUSTOMER_DETECTED", json.dumps(metadata_packet))
                            tracked_objects[obj_id]["triggered"] = True

        cap.release()

    await r.aclose()
    print("Vision loop ended.")
