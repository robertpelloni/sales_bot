import cv2
import json
import base64
import time
import asyncio
import redis.asyncio as redis
from collections import defaultdict
from ultralytics import YOLO

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Load YOLO model
model = YOLO('yolov8n.pt')

# Target properties
DWELL_TIME_THRESHOLD = 1.5
MIN_CONFIDENCE = 0.5
TRACK_HISTORY = defaultdict(lambda: [])
START_TIMES = {}

async def process_video_stream(video_source=0):
    cap = cv2.VideoCapture(video_source)

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Run YOLO inference
        results = model.track(frame, persist=True, classes=[0], conf=MIN_CONFIDENCE) # class 0 is person

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()

            for box, track_id in zip(boxes, track_ids):
                # We could calculate the distance based on box dimensions here if calibrated

                # Check for dwell time
                current_time = time.time()
                if track_id not in START_TIMES:
                    START_TIMES[track_id] = current_time
                elif current_time - START_TIMES[track_id] >= DWELL_TIME_THRESHOLD:
                    # Capture the target
                    x1, y1, x2, y2 = map(int, box)
                    cropped_frame = frame[max(0, y1):min(frame.shape[0], y2), max(0, x1):min(frame.shape[1], x2)]

                    if cropped_frame.size > 0:
                        # Encode image as JPEG
                        _, buffer = cv2.imencode('.jpg', cropped_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                        img_str = base64.b64encode(buffer).decode('utf-8')

                        # Extract pseudo-metadata
                        metadata = {
                            "id": track_id,
                            "attributes": ["a customer standing nearby"] # In real scenario, extract clothing colors etc.
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