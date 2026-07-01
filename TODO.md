# TODO

## Immediate
- [x] Implement actual LLM API client (OpenAI) in `src/llm_client.py` using `chat.completions.create(stream=True)`.
- [x] Add API Key configuration to `hub/templates/index.html` and `hub/main.py` so users can dynamically set their LLM keys.
- [x] Refactor `src/vision.py` to allow reading from a real camera device (`cv2.VideoCapture`) instead of a simulated loop. Add a "Mock Mode" flag for testing.
- [x] Expose Camera configuration (Device index/ID) in the Hub dashboard.

## Short-Term
- [ ] Add a visual log/feed to the Dashboard showing recently detected customers and the responses generated.
- [ ] Allow deleting items, tactics, and constraints from the UI.
- [ ] Add optional simulation parameter configuration (e.g. LLM temperature or explicit system prompt overrides) inside the Hub UI's "Simulate Detection" form for deeper A/B testing.
