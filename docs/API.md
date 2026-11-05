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
  "attributes": "navy blue windbreaker, carrying a backpack",
  "response": "Hey there! With that windbreaker, you look like you're ready for the elements. You should check out our waterproof boots..."
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

## 3. CRM & Lead Management Endpoints
Used internally by the Dashboard HTML forms to modify SQLite table rows.

### `POST /mark_lead/{interaction_id}`
Toggles the Boolean `is_lead` flag for a specific conversation event.
**Form Data:** `is_lead=True` or `is_lead=False`
**Response:** `303 See Other` redirect to `/`.

### `POST /update_follow_up/{interaction_id}`
Updates the string content of the `follow_up_notes` column.
**Form Data:** `follow_up_notes=Client requested a callback on Tuesday.`
**Response:** `303 See Other` redirect to `/`.

---

## 4. Configuration & Inventory Endpoints
*Note: All of these endpoints utilize the PRG (Post/Redirect/Get) pattern, returning a `303 See Other` redirect to the root `/` page upon success.*

### `POST /update_system_config`
Updates the runtime system toggles.
- `openai_api_key`: The secret key for Frontier models.
- `use_mock_vision`: `True` or `False`.

### `POST /add_item` / `POST /delete_item`
Manages the `config/inventory.json` catalog.
- **Add:** Requires `product_name`, `price_usd`, and `usps` (comma separated unique selling points).
- **Delete:** Requires `product_name`.

### `POST /add_tactic` / `POST /add_constraint`
Manages the `config/prompt_modifiers.json` AI psychology rulesets.
- **Add:** Requires `tactic` or `constraint` string.