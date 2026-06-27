# CHANGELOG
## [1.0.0] - Release Candidate & Containerization
- Fully containerized the edge-cloud pipeline using `Docker` and `docker-compose`.
- Bound container hardware interfaces to support Raspberry Pi camera passthrough.
- Updated `DEPLOY.md` with explicit orchestration instructions.

## [0.6.0] - Facial Embeddings for Repeat Customers
- Implemented mocked facial embedding extraction in `src/vision.py` to identify repeat customers using a Redis cache.
- Updated the LLM client to dynamically adjust its cold-open greeting if the customer is recognized as returning.

## [0.5.0] - Point-of-Sale Dynamic Pricing Integration
- Created `src/pos_client.py` mock service to simulate real-time POS stock levels.
- Updated LLM prompt compiler to fetch `live_inventory` and pass dynamic prices to the conversational model based on stock (scarcity premiums vs. fire sale discounts).
- Updated Vendor Dashboard to reflect dynamic live prices instead of static base config files.

## [0.4.1] - Hardware Acceleration Optimization
- Integrated GStreamer `libcamerasrc` pipeline for optimized Raspberry Pi 5 camera decoding, reducing CPU load and vision latency.

## [0.4.0] - A/B Testing Framework
- Implemented A/B testing dynamically assigning Aggressive vs. Empathetic cold-open strategies.
- Added strategy state-tracking into `analytics.db` funnel.
- Updated Vendor Dashboard to reflect A/B strategy conversion metrics.

## [0.3.1] - Distance Calibration
- Added strict distance calibration to `src/vision.py` using bounding box height metrics, requiring customers to be close to the kiosk to trigger.

## [0.3.0] - Vendor Dashboard Integration
- Added `src/dashboard.py` (FastAPI) allowing vendors to view real-time funnel analytics.
- Integrated dashboard webserver into the main event loop.

## [0.2.0] - Analytics & Conversational Upgrades
- Created `src/analytics.py` for SQLite tracking of the conversion funnel.
- Implemented real-time dynamic system prompts based on total conversion feedback loop.

## [0.1.1] - Minor Updates
- Integrated Piper TTS subprocess calls into `src/audio_output.py`.

## [0.1.0] - Initial Build
- Created core asynchronous orchestrator.
- Integrated YOLOv11 for local computer vision tracking.
- Set up streaming LLM client with OpenAI API.
- Implemented TTS chunking pipeline.
