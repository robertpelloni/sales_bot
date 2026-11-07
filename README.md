# Project Sirens / Sales Bot

Project Sirens is an Automated Proactive Conversational Sales Agent designed to run on embedded hardware like a Raspberry Pi 5. Its ultimate goal is to capture attention, build instant rapport, identify friction points, and close sales using advanced conversational framework strategies without requiring an active trigger from the user. It uses real-time computer vision to identify customers, extract visual attributes, and engage them with highly contextualized, personalized, and persuasive audio pitches with sub-second latency.

## Architecture

The system utilizes an asynchronous, decoupled **Edge-Cloud Split Architecture** running concurrently across microservices managed by Docker Swarm.

*   **IPC Bus (Redis):** Handles real-time messaging between microservices globally using `pub/sub` across unique `NODE_ID` environments.
*   **Vision Engine (`src/vision.py`):** Runs YOLOv11 tracking to identify human bounding boxes. Employs distance calibration and uses facial embeddings to identify repeat customers. Runs heavily optimized frame-skipping with GStreamer hardware acceleration for Raspberry Pi.
*   **Conversational Agent (`src/llm_client.py`):** Handles streaming integration with OpenAI's `gpt-4o-mini`. Translates visual attributes into "cold open" Pattern Interrupts and handles stateful memory to support multi-turn dialogues with dynamic A/B strategy assignments.
*   **Audio Pipeline (`src/audio_input.py` & `src/audio_output.py`):** Captures customer STT replies and chunks the streaming LLM outputs into sentences to feed the C++ Piper TTS engine natively via `aplay`.
*   **Analytics Hub (`src/analytics.py` & `src/dashboard.py`):** Acts as the central node server, aggregating metrics from all active kiosks into an SQLite `analytics.db` database and exposing them via a rich visual FastAPI dashboard using `Chart.js`.
*   **Point-of-Sale (`src/pos_client.py`):** Actively injects dynamic pricing models (scarcity premiums and fire-sale discounts) based on live inventory stocks into the VLM prompt.

## Setup Instructions

### Environment Configuration
You must provide an OpenAI API key.
```bash
export OPENAI_API_KEY="your-key-here"
```

### 1. Docker Compose (Recommended)
You can orchestrate the full pipeline (including a Redis instance, the Central Hub, and two mock Edge Kiosks) instantly. Ensure your webcam is connected as the Compose maps `/dev/video0`.

```bash
# Clone with required dependencies
git clone --recursive https://github.com/robertpelloni/sales_bot.git
cd sales_bot

# Build and start the cluster
docker-compose up --build -d
```

### 2. Bare-Metal Execution
```bash
sudo apt-get install redis-server build-essential cmake libgl1-mesa-glx alsa-utils
pip install -r requirements.txt
redis-server --daemonize yes

# Start the application using argparse modes
python3 -m src.main --mode all
```

## Running the Benchmark / Demo
To verify that the OpenAI LLM connection is functioning and to measure the core architectural latency (Time-To-First-Audio), you can run the benchmark script. This script mocks a camera detection payload and publishes it directly into the Redis pipeline.

1. Ensure Redis is running (or your Docker stack is up).
2. Start the core edge node services:
   ```bash
   NODE_ID=kiosk_benchmark python3 -m src.main --mode edge
   ```
3. In another terminal, run the benchmark simulation:
   ```bash
   NODE_ID=kiosk_benchmark python3 -m src.demo_benchmark
   ```

The benchmark will output the time (in milliseconds) it took for the system to process the detection, query the frontier model, and generate the first speakable sentence chunk.

## Configuration Guide

The behavior and knowledge base of the sales agent are entirely driven by local JSON configurations located in the `config/` directory.

### `config/inventory.json`
This file acts as the primary knowledge base for the LLM. It defines the store's name and the products available for sale.
*   **`product_name`**: The exact name of the item.
*   **`price_usd`**: The baseline price of the item.
*   **`unique_selling_points`**: A list of key features and benefits the LLM will draw upon to handle objections and build value during the pitch.

### `config/prompt_modifiers.json`
This file dictates the psychological framework and behavioral guardrails the LLM must adhere to.
*   **`sales_framework`**: Defines the overarching strategy (e.g., "Pattern Interrupt Cold-Open").
*   **`tactics_enforced`**: Specific closing techniques or pacing rules (e.g., "Assumptive close formatting").
*   **`constraints`**: Absolute rules the model must not break (e.g., "Never use generic store greetings like 'Welcome to our store'").

## Usage Guide & Dashboard

Once the services are running, the **Analytics Hub** provides a centralized view of system performance and active kiosk status.

1.  Open a web browser and navigate to `http://localhost:8000`.
2.  The dashboard provides real-time visualizations of:
    *   **Conversion Funnel:** Track the number of customers approached, engaged, objections raised, and successful conversions.
    *   **A/B Strategy Performance:** Compare the win rates of different system prompt strategies (e.g., Aggressive vs. Empathetic cold opens).
    *   **Live POS Inventory:** View the current stock levels and active pricing modifiers injected by the POS client simulator.

The system will automatically begin scanning via `/dev/video0`. When a person is detected dwelling in the frame, the edge pipeline will extract attributes, query the LLM, and output the customized audio pitch via the default system audio device.
