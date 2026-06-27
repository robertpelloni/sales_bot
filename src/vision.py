import cv2
import json
import base64
import time
import asyncio
import random
import numpy as np
import redis.asyncio as redis
import os
from collections import defaultdict
from ultralytics import YOLO

# Connect to Redis
r = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379, db=0)

NODE_ID = os.environ.get('NODE_ID', 'kiosk_default')

# Load YOLO model
model = YOLO('yolov11n.pt')

# Target properties
DWELL_TIME_THRESHOLD = 1.5
MIN_CONFIDENCE = 0.5
MIN_PROXIMITY_RATIO = 0.6  # Bounding box must occupy 60% of frame height
TRACK_HISTORY = defaultdict(lambda: [])
START_TIMES = {}

try:
    import face_recognition
    FACE_REC_AVAILABLE = True
except ImportError:
    FACE_REC_AVAILABLE = False
    print("[Vision] face_recognition library not found. Falling back to mocked embeddings.")

class FaceEmbedding:
    @staticmethod
    def get_embedding(frame):
        if FACE_REC_AVAILABLE:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Find face locations
            face_locations = face_recognition.face_locations(rgb_frame)
            if face_locations:
                # Get the embedding for the first face found
                encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                if encodings:
                    return encodings[0].tolist()
            return None
        else:
            # Return a mock 128D embedding vector for testing environments
            return np.random.rand(128).tolist()

    @staticmethod
    def is_match(embed1, embed2, threshold=0.6):
        if not embed1 or not embed2:
            return False

        if FACE_REC_AVAILABLE:
            # face_recognition uses a slightly different distance calc natively but we can use np
            dist = np.linalg.norm(np.array(embed1) - np.array(embed2))
            return dist < threshold
        else:
            return False

def capture_and_track(cap):
    success, frame = cap.read()
    if not success:
        return False, None, None
    results = model.track(frame, persist=True, classes=[0], conf=MIN_CONFIDENCE) # class 0 is person
    return True, frame, results

def get_gstreamer_pipeline():
    # Raspberry Pi specific hardware-accelerated libcamera pipeline
    return (
        "libcamerasrc ! "
        "video/x-raw, width=640, height=480, framerate=30/1 ! "
        "videoconvert ! appsink"
    )

async def check_repeat_customer(embedding):
    """
    Checks the Redis cache of known customer embeddings asynchronously using batches.
    If a match is found, returns True. Otherwise, saves the new embedding and returns False.
    """
    try:
        if embedding is None:
            return False

        # Use SCAN to iterate without blocking redis, though keys is small usually.
        cursor = b'0'
        while cursor:
            cursor, keys = await r.scan(cursor=cursor, match="customer_embed:*", count=100)

            # Redis SCAN can return 0 keys with a valid cursor, only process if keys exist
            if keys:
                # Fetch batch of embeddings
                stored_embed_strs = await r.mget(keys)

                for stored_embed_str in stored_embed_strs:
                    if stored_embed_str:
                        stored_embed = json.loads(stored_embed_str.decode('utf-8'))
                        if FaceEmbedding.is_match(embedding, stored_embed):
                            return True

        # No match found, save new customer securely with INCR to avoid race conditions
        new_id = await r.incr("customer_id_counter")
        # Set an expiration so the database doesn't grow unbounded in production (e.g. 7 days)
        await r.set(f"customer_embed:{new_id}", json.dumps(embedding), ex=604800)
        return False
    except Exception as e:
        print(f"[Vision] Error checking repeat customer: {e}")
        return False

async def process_video_stream(video_source=0):
    # Attempt hardware acceleration using GStreamer if a numeric ID is given
    if isinstance(video_source, int):
        cap = cv2.VideoCapture(get_gstreamer_pipeline(), cv2.CAP_GSTREAMER)
        # Fallback to standard V4L2 if GStreamer fails (e.g. testing environments)
        if not cap.isOpened():
            print("[Vision] GStreamer failed. Falling back to standard V4L2 capture.")
            cap = cv2.VideoCapture(video_source)
    else:
        # E.g. reading from a file or mock string
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

                        # Process Facial Embedding to check for Repeat Customer
                        face_embedding = FaceEmbedding.get_embedding(cropped_frame)
                        is_repeat = await check_repeat_customer(face_embedding)

                        # Extract pseudo-metadata
                        metadata = {
                            "id": track_id,
                            "attributes": ["a customer standing nearby"], # In real scenario, extract clothing colors etc.
                            "strategy": strategy,
                            "is_repeat_customer": is_repeat,
                            "node_id": NODE_ID
                        }

                        payload = {
                            "metadata": metadata,
                            "image_b64": img_str
                        }

                        # Emit event on NODE specific channel
                        await r.publish(f'CUSTOMER_DETECTED:{NODE_ID}', json.dumps(payload))
                        print(f"Customer {track_id} locked. Triggering event on {NODE_ID}. Repeat: {is_repeat}")

                        # Reset tracking to avoid spamming
                        START_TIMES[track_id] = current_time + 60 # Cooldown

        await asyncio.sleep(0.01) # Small sleep to avoid blocking

if __name__ == "__main__":
    asyncio.run(process_video_stream())
