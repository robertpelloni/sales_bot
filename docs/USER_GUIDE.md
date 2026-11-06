# Project Sirens - User Guide

Welcome to the Project Sirens Hub. This interface is the central command center for your autonomous retail agent. The dashboard allows you to define what the agent sells, how the agent speaks, test cold open pitches, and review how it is performing in the real world.

## Accessing the Hub
Start the Hub using the server management script:
```bash
./scripts/manage_servers.sh start-hub
```
Then open your browser to **`http://localhost:8000`**.
*(Default login: `admin` / `password`)*

---

## 1. Top Header & System Controls
The unified header bar provides real-time visibility into the system:
- **Hub Status**: Confirms whether the FastAPI backend is online.
- **Vision Engine**: Displays whether the system is in Mock Mode or actively polling a physical hardware camera (e.g. `/dev/video0`).
- **LLM Engine**: Indicates whether the streaming VLM API key is configured.
- **Quit Server Button**: Allows safely shutting down the server process directly from the UI.

---

## 2. Desktop System Tray App
Project Sirens includes a native desktop taskbar tray controller (`src/tray_app.py`):
- Run with: `./scripts/run_tray.sh`
- Click the tray icon to quickly open the dashboard in your default browser.
- Start or stop the Hub and Kiosk services independently.
- Use **Quit All & Exit** to terminate all background pipelines gracefully.
- Runs with full headless fallback if launched in headless or containerized environments.

---

## 3. Running Detection Simulations (High-Value Testing)
The **Simulation & Cold-Open Engine** allows instant A/B testing:
1. Enter mock visual traits in **Simulated Customer Profile Attributes** (e.g. *"navy blue windbreaker, baseball cap, holding coffee"*).
2. Adjust **Temperature** for creativity (lower for deterministic pitches, higher for spontaneous banter).
3. Optionally provide a **Prompt Override** to test custom sales strategies.
4. Click **Run Instant Detection & Generate Pitch** to see the agent's response immediately.

---

## 4. Live CRM Feed & Visual Analytics
Every customer interaction is streamed and persisted in `sirens.db`:
- **Interaction Charts**: Chart.js graphs track conversation volume over the past 7 days and sales framework conversion efficiency.
- **Lead Qualification**: Click **Flag as Qualified Lead** on any successful pitch.
- **Staff Pitch Ratings**: Rate cold opens with 👎 or 👍 to tune sales rules.
- **Follow-up Notes**: Add staff notes directly to customer interaction cards.
- **Exporting CRM Leads & Logs (CSV)**: Click **Export Leads (CSV)** to stream and download all flagged qualified leads directly into an RFC 4180 CSV spreadsheet. To export every customer interaction log regardless of lead qualification, click **All Logs**.
- **Automated A/B Sales Framework Optimization**: Inspect live empirical win rates, Beta prior parameters ($\alpha, \beta$), and 95% confidence intervals per sales framework. Tune algorithm routing strategies (Thompson Sampling, Upper Confidence Bound UCB1, or Epsilon-Greedy with geometric decay) and exploration parameters directly from the dashboard card.
- **Contextual Vision Affinity Routing**: Enable contextual weighting in the Bandit Algorithmic Tuning panel. When enabled, the Multi-Armed Bandit dynamically biases framework selection based on optical vision tracking:
  - *Close Proximity (≤1.2m)*: Biases toward Assumptive Close Narrative and Challenger Sales Framework.
  - *Far Distance (>2.5m)*: Biases toward Pattern Interrupt Cold-Open to turn passing pedestrian heads.
  - *High Dwell (≥10s)*: Biases toward Consultative Problem-Solver for customers actively browsing.

---

## 5. Knowledge Base & Sales Psychology Settings
- **Product Inventory**: Add products with price and Unique Selling Points (USPs). Delete products with a single click.
- **Store Identity**: Set the store name dynamically.
- **Sales Psychology Modifiers**:
  - Add or delete **Tactics Enforced** (e.g. *"Use assumptive close formatting"*).
  - Add or delete **Privacy & Behavioral Constraints** (e.g. *"Never mention brand names"*).
- **Hardware Connection**: Update `OPENAI_API_KEY`, Camera index, and toggle between Mock and Live Vision modes.

---

## 6. External CRM Webhook Relay (Salesforce, HubSpot, Zapier)
Project Sirens automatically forwards real-time retail events to enterprise CRMs and marketing automation platforms without stalling the edge pipeline:
- **Enable Webhook Forwarding**: Toggle the active status switch in the External CRM Webhook Relay card.
- **Webhook Destination URL**: Provide an HTTPS endpoint (e.g., Salesforce/HubSpot ingest hook or Zapier trigger).
- **HMAC Secret Key**: Specify a secret signing key. Each dispatched HTTP request includes an `X-Sirens-Signature: sha256=<hex_digest>` header computed over the JSON payload for cryptographic verification.
- **Event Filtering**: Check which lifecycle events should trigger dispatches (`New Interactions`, `Qualified Leads Flagged`, `Staff Feedback Recorded`).
- **Send Test Ping**: Click the test ping button to immediately fire an asynchronous mock test payload and verify external connectivity and signature validation.
