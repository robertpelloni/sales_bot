# Project Sirens - API Documentation

The Sirens Hub API is built on FastAPI. It serves dual purposes: rendering the unified HTML dashboard for user interaction, and providing JSON webhook endpoints for the edge Kiosk to stream data.

## Base URL
When running locally via `docker-compose` or `uvicorn`, the Hub API is accessible at:
`http://localhost:8000`

---

## 1. Edge Integration Endpoints
These endpoints are designed to be consumed by the edge hardware (the `kiosk` process) running the vision tracker and VLM clients.

### `POST /api/log_interaction`
Webhook designed to log the completed conversation strings and visual attributes into the local SQLite CRM database (`sirens.db`).

**Content-Type:** `application/json`
**Request Body:**
```json
{
  "status": "healthy",
  "service": "Project Sirens Hub",
  "version": "0.8.0",
  "mock_vision": true,
  "camera_index": "0",
  "has_openai_key": false,
  "inventory_item_count": 3
}
```

**Responses:**
- `200 OK`: Returns `{"status": "success", "id": <interaction_id>}`.
- `500 Internal Server Error`: Returns if database insertion or SQLAlchemy rollback fails.

---

## 2. Simulation & Testing Endpoints
These endpoints are utilized by the Hub UI to allow rapid A/B testing of the VLM logic without requiring actual physical vision events or Redis routing.

### `POST /simulate_detection`
Invokes the core `src/llm_client.py` logic natively within the Hub container. It bypasses Redis and returns the parsed string directly.

**Content-Type:** `application/x-www-form-urlencoded`
**Form Data Parameters:**
- `attributes` (string): Comma-separated visual traits to pass to the model (e.g., "red hat, sunglasses").
- `system_prompt_override` (string): Optional text to completely replace the standard `inventory.json` framework context.
- `temperature` (float): Standard OpenAI sampling temperature (default: `0.8`).

**Responses:**
- `303 See Other`: Redirects back to `/` rendering the dashboard with the generated response injected into the template variables.

---

### 9. `GET /api/ab/allocations`
- **Description**: Retrieves real-time Multi-Armed Bandit framework allocation metrics, Bayesian priors, win rates, and trial counts.
- **Query Parameter**: `method` (`thompson` or `epsilon_greedy`, default: `thompson`).
- **Response**:
```json
{
  "method": "thompson",
  "recommended_framework": "Challenger Sales Framework",
  "arms": {
    "Challenger Sales Framework": {
      "trials": 15,
      "leads": 6,
      "win_rate": 0.4,
      "feedback_sum": 4,
      "alpha": 7.0,
      "beta": 10.0
    }
  }
}
```

### 10. `POST /api/ab/select_framework`
- **Description**: Dynamically requests the bandit algorithm to allocate a sales framework for an incoming customer interaction.
- **Query Parameter**: `method` (`thompson` or `epsilon_greedy`, default: `thompson`).
- **Response**:
```json
{
  "framework": "Challenger Sales Framework",
  "method": "thompson",
  "trials": 15,
  "win_rate": 0.4
}
```
