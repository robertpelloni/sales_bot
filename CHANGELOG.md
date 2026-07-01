# CHANGELOG

## [0.2.0] - LLM Integration & System Config
- Integrated OpenAI API client for live VLM streams, overriding mock logic when `OPENAI_API_KEY` is present.
- Refactored `start_vision_loop` to attempt `cv2.VideoCapture(0)` hardware mapping when `USE_MOCK_VISION` is false.
- Added System Configuration routing to the Hub API for runtime toggle of hardware mocks and live API keys.
- Enhanced `tests/test_conversation.py` to prevent environment variables from bleeding into assertions.

## [0.1.1] - Hub UI Array Enhancements
- Expanded Hub HTML template with comprehensive form components for Inventory Items, Tactics Enforced, and Constraints.
- Added descriptive tooltips to all configuration elements.

## [0.1.0] - Initial Setup
- Initialized documentation files
- Set up directory structure and configurations
- Added git submodules (vendor/piper, vendor/yolov11-edge)
- Created docker-compose infrastructure
- Implemented core components: hub, main orchestrator, vision, llm_client, and audio_output

## [0.2.1] - Integration Testing & Follow-Ups
- Built complete E2E `pytest` integration test pipeline to protect Hub UI routes (`tests/test_api.py`).
- Documented follow-up requirements inside `TODO.md` for extended simulation testing parameters.
