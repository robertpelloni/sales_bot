import asyncio
import base64
import json
import os
import time
from typing import Any, Tuple

import cv2
import numpy as np
import redis.asyncio as redis

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

try:
    from llm_client import get_system_config
except ImportError:
    from src.llm_client import get_system_config


class MockYOLO:
    """Mock YOLO detector for environments without physical edge TPU or camera hardware."""

    def __init__(self, model_name: str = "yolo11n.pt"):
        self.model_name = model_name

    def track(self, frame: Any, persist: bool = True):
        class MockResult:
            def __init__(self):
                self.boxes = type(
                    "Boxes",
                    (),
                    {
                        "id": [1],
                        "xyxy": [[100, 100, 200, 200]],
                        "conf": [0.9],
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
    # 1. Edge TPU compiled TFLite model check
    if os.path.exists(model_path):
        try:
            print(f"Loading Coral Edge TPU optimized model: {model_path}")
            model = YOLO(model_path)
            return model, "coral_edgetpu"
        except Exception as e:
            print(f"Warning: Failed to initialize Coral Edge TPU model: {e}")

    # 2. Standard PyTorch model fallback
    if os.path.exists(pytorch_fallback):
        try:
            print(f"Loading standard PyTorch model: {pytorch_fallback}")
            model = YOLO(pytorch_fallback)
            return model, "pytorch"
        except Exception as e:
            print(f"Warning: Failed to initialize PyTorch model: {e}")

    # 3. Deterministic Mock fallback
    print("Falling back to MockYOLO tracker.")
    return MockYOLO(model_name=pytorch_fallback), "mock"


async def start_vision_loop(redis_url: str):
    r = redis.from_url(redis_url)
    print("Vision system initializing hardware bindings...")

    _, use_mock_vision_str = get_system_config()
    use_mock_vision = use_mock_vision_str.lower() in ("true", "1", "yes")

    model, model_type = load_vision_model()
    if model_type == "mock":
        use_mock_vision = True

    print(f"Vision system started using engine: {model_type} (mock_mode={use_mock_vision})")

    tracked_objects = {}
    last_cleanup_time = time.time()

    if use_mock_vision:
        # Mock vision loop
        for i in range(10):
            await asyncio.sleep(1)
            current_time = time.time()

            # Privacy Directive: Delete bounding box memory buffers every 60 seconds
            if current_time - last_cleanup_time > 60:
                tracked_objects.clear()
                last_cleanup_time = current_time
                print("Vision: Cleared bounding box memory buffers (Privacy Directive).")

            obj_id = 1

            if obj_id not in tracked_objects:
                tracked_objects[obj_id] = {"first_seen": current_time}

            if current_time - tracked_objects[obj_id]["first_seen"] > 1.5:
                if not tracked_objects[obj_id].get("triggered", False):
                    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    _, buffer = cv2.imencode(
                        ".jpg", dummy_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50]
                    )
                    encoded_frame = base64.b64encode(buffer).decode("utf-8")

                    metadata_packet = {
                        "id": obj_id,
                        "proximity": "1.2m",
                        "attributes": ["navy blue windbreaker", "baseball cap", "holding coffee"],
                        "frame_data": encoded_frame,
                    }

                    print(f"Vision: Detected customer ID {obj_id}. Publishing to Redis.")
                    await r.publish("CUSTOMER_DETECTED", json.dumps(metadata_packet))
                    tracked_objects[obj_id]["triggered"] = True
    else:
        # Real vision loop using cv2.VideoCapture
        cap = cv2.VideoCapture(0)

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            await asyncio.sleep(0.01)
            current_time = time.time()

            # Privacy Directive: Delete bounding box memory buffers every 60 seconds
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
                for box, obj_id_tensor in zip(results[0].boxes, results[0].boxes.id):
                    obj_id = int(obj_id_tensor.item())

                    if obj_id not in tracked_objects:
                        tracked_objects[obj_id] = {"first_seen": current_time}

                    if current_time - tracked_objects[obj_id]["first_seen"] > 1.5:
                        if not tracked_objects[obj_id].get("triggered", False):
                            # Proximity lock triggered - compress frame for VLM payload
                            _, buffer = cv2.imencode(
                                ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50]
                            )
                            encoded_frame = base64.b64encode(buffer).decode("utf-8")

                            metadata_packet = {
                                "id": obj_id,
                                "proximity": "locked",
                                "attributes": ["customer"],
                                "frame_data": encoded_frame,
                            }

                            print(
                                f"Vision: Detected live customer ID {obj_id}. Publishing to Redis."
                            )
                            await r.publish("CUSTOMER_DETECTED", json.dumps(metadata_packet))
                            tracked_objects[obj_id]["triggered"] = True

        cap.release()

    await r.aclose()
    print("Vision loop ended.")
