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

---

## 5. Reviewing CRM Logs & Analytics
Every time the agent speaks to a customer (whether live in-store or via the simulation engine), the interaction is logged in the **Live Interaction Log & Analytics** panel.

- **The Chart:** A visual line graph automatically tracks the volume of conversations generated over the last 7 days.
- **Tracking Leads:** If an interaction was particularly successful, click the green **Mark as Lead** button beneath the interaction card. This flags the engagement as a `Qualified Lead`.
- **Follow-up Notes:** Type reminders or action items into the text box beneath a logged interaction and click **Save Note**. These notes are saved permanently to the database so you can review them later.