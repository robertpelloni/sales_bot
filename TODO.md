# TODO

## Immediate
- [x] Implement actual LLM API client (OpenAI) in `src/llm_client.py` using `chat.completions.create(stream=True)`.
- [x] Add API Key configuration to `hub/templates/index.html` and `hub/main.py` so users can dynamically set their LLM keys.
- [x] Refactor `src/vision.py` to allow reading from a real camera device (`cv2.VideoCapture`) instead of a simulated loop. Add a "Mock Mode" flag for testing.
- [x] Expose Camera configuration (Device index/ID) in the Hub dashboard.

## Short-Term
- [x] Add a visual log/feed to the Dashboard showing recently detected customers and the responses generated.
- [x] Allow deleting items, tactics, and constraints from the UI.
- [x] Add optional simulation parameter configuration (e.g. LLM temperature or explicit system prompt overrides) inside the Hub UI's "Simulate Detection" form for deeper A/B testing.

## Medium-Term
- [x] Add visual analytics (graphs/charts) to the Dashboard tracking conversation frequency over time.
- [x] Incorporate text-to-speech feedback logs (e.g., latency of Piper generation) into the interaction database for performance tuning.

## Maintenance / Tech Debt
- [x] Refactor Hub Dashboard to use `aiosqlite` and asynchronous SQLAlchemy database sessions. Current performance benchmarks show synchronous SQLAlchemy blocking the `uvicorn` event loop, causing p95 latency to exceed the 200ms target during high concurrency (1000+ simultaneous webhook hits).
- [x] Investigate minor package updates available in PyPI: `fastapi` -> 0.139.0, `playwright` -> 1.61.0, `greenlet` -> 3.5.3, `pydantic_core` -> 2.47.0.
