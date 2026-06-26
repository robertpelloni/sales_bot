import cv2
import json
import base64
import time
import asyncio
import random
import redis.asyncio as redis
from collections import defaultdict
from ultralytics import YOLO

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Load YOLO model
model = YOLO('yolov11n.pt')

# Target properties
DWELL_TIME_THRESHOLD = 1.5
MIN_CONFIDENCE = 0.5
MIN_PROXIMITY_RATIO = 0.6  # Bounding box must occupy 60% of frame height
TRACK_HISTORY = defaultdict(lambda: [])
START_TIMES = {}

def capture_and_track(cap):
    success, frame = cap.read()
    if not success:
        return False, None, None
    results = model.track(frame, persist=True, classes=[0], conf=MIN_CONFIDENCE) # class 0 is person
    return True, frame, results

async def process_video_stream(video_source=0):
    cap = cv2.VideoCapture(video_source)

    while cap.isOpened():
        success, frame, results = await asyncio.to_thread(capture_and_track, cap)
        if not success:
            break

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()

            for box, track_id in zip(boxes, track_ids):
                x1, y1, x2, y2 = map(int, box)
                box_height = y2 - y1
                frame_height = frame.shape[0]

                # Proximity calculation
                proximity_ratio = box_height / float(frame_height)

                # Check for dwell time and proximity
                current_time = time.time()
                if track_id not in START_TIMES:
                    if proximity_ratio >= MIN_PROXIMITY_RATIO:
                        START_TIMES[track_id] = current_time
                elif current_time - START_TIMES[track_id] >= DWELL_TIME_THRESHOLD:
                    if proximity_ratio < MIN_PROXIMITY_RATIO:
                        # Reset tracking if they back away
                        del START_TIMES[track_id]
                        continue

                    # Capture the target
                    cropped_frame = frame[max(0, y1):min(frame.shape[0], y2), max(0, x1):min(frame.shape[1], x2)]

                    if cropped_frame.size > 0:
                        # Encode image as JPEG
                        _, buffer = cv2.imencode('.jpg', cropped_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                        img_str = base64.b64encode(buffer).decode('utf-8')

                        # Assign A/B Testing Strategy
                        strategy = "A_AGGRESSIVE" if random.random() > 0.5 else "B_EMPATHETIC"

                        # Extract pseudo-metadata
                        metadata = {
                            "id": track_id,
                            "attributes": ["a customer standing nearby"], # In real scenario, extract clothing colors etc.
                            "strategy": strategy
                        }

                        payload = {
                            "metadata": metadata,
                            "image_b64": img_str
                        }

                        # Emit event
                        await r.publish('CUSTOMER_DETECTED', json.dumps(payload))
                        print(f"Customer {track_id} locked. Triggering event.")

                        # Reset tracking to avoid spamming
                        START_TIMES[track_id] = current_time + 60 # Cooldown

        await asyncio.sleep(0.01) # Small sleep to avoid blocking

if __name__ == "__main__":
    asyncio.run(process_video_stream())