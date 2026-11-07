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
  "version": "1.5.0",
  "mock_vision": true,
  "camera_index": "0",
  "has_openai_key": false,
  "inventory_item_count": 2,
  "active_promotions_count": 2
}
```

### 3. `POST /add_promotion`
- **Description**: Registers a dynamic promotional discount rule into the active inventory configuration.
- **Form Parameters**:
  - `rule_name`: Identifier for the promotion (e.g. `Rainy Day Flash Sale`).
  - `discount_percent`: Percentage discount offered (0.0 to 100.0).
  - `trigger_type`: Contextual trigger (`all_items`, `weather_or_apparel`, `dwell_time`, `volume_units`).
  - `threshold`: Condition requirement (e.g. `outerwear`, `30s`, `2+ units`).
  - `description`: LLM pitch guidance instructing the model how and when to present the discount.

### 4. `POST /delete_promotion/{promo_index}`
- **Description**: Removes an active promotion by its zero-based index and redirects back to the dashboard.

### 3. `WebSocket /ws/events`
- **Description**: Real-time duplex WebSocket stream. On connection, clients receive live push events broadcast whenever new customer interactions are captured or logged.
- **Message Type**: JSON
- **Payload Schema**:
```json
{
  "type": "new_interaction",
  "data": {
    "id": 105,
    "detected_attributes": "navy blue windbreaker, baseball cap",
    "dialogue": "Handcrafted windbreakers on special today!",
    "strategy": "Pattern Interrupt",
    "timestamp": "2026-11-05 05:00:00",
    "tts_latency": "115ms",
    "is_lead": false,
    "rating": 1,
    "follow_up": null
  }
}
```

### 15. `GET /api/webhooks/config`
- **Description**: Retrieves current outbound CRM webhook relay configuration (enabled status, destination URL, secret key presence, subscribed events).
- **Response**:
```json
{
  "enabled": true,
  "url": "https://api.crm.example.com/v1/leads",
  "secret_key": "sirens_sec_...",
  "events": ["NEW_INTERACTION", "LEAD_QUALIFIED"],
  "timeout_seconds": 5
}
```

### 16. `POST /api/webhooks/config`
- **Description**: Updates outbound CRM webhook destination, secret verification key, and subscribed events.
- **Request Body**:
```json
{
  "enabled": true,
  "url": "https://hooks.zapier.com/hooks/catch/123/abc",
  "secret_key": "custom_secret_key",
  "events": ["LEAD_QUALIFIED"],
  "timeout_seconds": 5
}
```

### 17. `POST /api/webhooks/test`
- **Description**: Dispatches a live test mock payload asynchronously to the configured webhook endpoint, generating an HMAC-SHA256 signature.
- **Response**:
```json
{
  "status": "dispatched",
  "event": "TEST_PING",
  "url": "https://api.crm.example.com/v1/leads",
  "signature_header": "X-Sirens-Signature: sha256=...",
  "message": "Test webhook payload dispatched asynchronously."
}
```

### 3. `POST /api/server/shutdown`
- **Description**: Gracefully terminates the Hub server process after acknowledging the request.
- **Response**:
```json
{
  "status": "shutting_down",
  "message": "Hub server is shutting down gracefully."
}
```

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
- **Description**: Dynamically requests the bandit algorithm to allocate a sales framework for an incoming customer interaction, supporting vision context (dwell time and proximity distance).
- **Query Parameters**:
  - `method`: `thompson`, `epsilon_greedy`, or `ucb1`.
  - `dwell_time_s`: (Optional) Customer dwell time in seconds.
  - `distance_m`: (Optional) Calibrated spatial distance in meters.
- **Response**:
```json
{
  "status": "success",
  "selected_framework": "Consultative Problem-Solver",
  "method": "thompson",
  "conversion_rate": 35.0,
  "context_affinity": 1.5
}
```

### 11. `GET /api/leads/export`
- **Description**: Streams RFC 4180-compliant CSV data containing customer CRM interaction logs.
- **Query Parameter**: `all` (boolean, default: `false`). When `true`, exports all interaction logs. When `false`, exports only flagged qualified leads (`is_lead == True`).
- **Response Headers**: `Content-Type: text/csv; charset=utf-8`, `Content-Disposition: attachment; filename="crm_leads.csv"`

### 12. `GET /api/analytics/summary`
- **Description**: Returns aggregated statistical metrics across all recorded CRM customer interactions.
- **Response**:
```json
{
  "total_interactions": 42,
  "qualified_leads": 14,
  "conversion_rate_percent": 33.33,
  "avg_tts_latency_ms": 118.5,
  "avg_feedback_score": 4.2
}
```

### 13. `POST /api/ab/config`
- **Description**: Dynamically configures hyperparameters for the Multi-Armed Bandit optimization engine.
- **Payload**:
```json
{
  "epsilon": 0.20,
  "decay_rate": 0.99,
  "min_epsilon": 0.05,
  "default_method": "thompson",
  "contextual_weighting": true
}
```
- **Response**:
```json
{
  "status": "success",
  "config": {
    "epsilon": 0.20,
    "decay_rate": 0.99,
    "min_epsilon": 0.05,
    "default_method": "thompson"
  }
}
```

### 14. `POST /api/ab/reset`
- **Description**: Resets the bandit's exploration epsilon and clears in-memory prior overrides to initial values.
- **Response**:
```json
{
  "status": "success",
  "message": "Multi-Armed Bandit parameters and prior overrides reset successfully",
  "config": {
    "epsilon": 0.20,
    "decay_rate": 0.99,
    "min_epsilon": 0.05,
    "default_method": "thompson"
  }
}
```
