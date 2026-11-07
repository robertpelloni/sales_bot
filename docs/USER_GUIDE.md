# Project Sirens - User Guide

Welcome to the Project Sirens Hub. This interface is the central nervous system for your autonomous retail agent. The dashboard allows you to define what the agent sells, how the agent speaks, and review how it is performing in the real world.

## Accessing the Hub
Once the `docker-compose` stack is running, open a web browser and navigate to:
**`http://localhost:8000`**

The interface is divided into two primary sections: **Operations & Logs** (Left Column) and **Configuration & Knowledge Base** (Right Column).

---

## 1. System Configuration
Before the agent can generate responses, it requires an intelligence engine.
1. Scroll to the **System Configuration** panel on the right side.
2. Enter your `OPENAI_API_KEY`.
3. If you do not have physical cameras attached to your deployment hardware, ensure **Mock Hardware Vision** is set to `True`.
4. Click **Update System Config**. *(Note: This data is stored locally on your device and is never transmitted anywhere except directly to OpenAI during a generation request).*

---

## 2. Managing Inventory
The agent can only pitch products it knows about. You can manage this via the **Knowledge Base: Inventory** panel.
- **Adding Items:** Enter the product's name, price, and a comma-separated list of "Unique Selling Points" (e.g., *Waterproof, 40hr Battery, Vegan Leather*). Click **Add Item**.
- **Deleting Items:** Click the red **Delete** button next to an existing item card.

---

## 3. Controlling Sales Psychology
The agent's personality is controlled via the **Agent Prompt Modifiers** panel.
- **Sales Framework:** A high-level instruction defining the agent's tone. (e.g., *"Pattern Interrupt Cold-Open"* or *"Friendly Consultative Approach"*).
- **Tactics:** Specific psychological strategies the agent must attempt to weave into its dialogue. Try adding things like *"Use assumptive close formatting"* or *"Create perceived scarcity"*.
- **Constraints:** Strict boundaries the agent must never cross. Try adding things like *"Never mention exact clothing brands to avoid being creepy"* or *"Keep responses under 3 sentences"*.

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
