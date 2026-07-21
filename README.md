# sales_bot

please come up with a design and extremely detailed plan to create a raspberry pi powered (or some other embedded system) smart speaker/camera system that vendors can place in their shops which identifies customers walking by with computer vision, calls them out based on what they are wearing and tries to persuade them into conversation where it tries to sell them on any goods they are configured to sell based on all the information and selling points about those goods, using everything a frontier llm model knows about salesmanship and selling techiques and proven strategies about dealing with customers, come up with an extremely detailed plan to enhance it in every way possible in order to instill all the most successful selling and marketing strategies into it in order to make it the most persuasive possible sales agent  

Building an autonomous, AI-driven interactive sales agent on embedded hardware requires combining real-time computer vision, low-latency conversational AI, and advanced behavioral psychology.

Because standard large-scale models are too slow to run directly on an ARM-based microcontroller with zero lag, a hybrid Edge-Cloud Split Architecture is ideal. Computer vision, wake-word detection, and audio processing run entirely locally at the edge to track motion and ingest data instantly, while a low-latency Frontier Vision-Language Model (VLM) API processes the visual features and dictates the sales engine in real-time.

Here is the blueprints and implementation plan for Project Sirens (Automated Proactive Conversational Sales Agent).

1. System Hardware Architecture
The core objective is to minimize total loop latency (the time from a customer walking into frame to a highly specific vocal greeting) to under 1.2 seconds.

Component	Choice	Justification
Compute Unit	Raspberry Pi 5 (8GB)	Provides the PCIe bandwidth needed for high-speed peripherals and the multi-core CPU overhead necessary to manage real-time multi-threaded Python loops.
Visual Sensor	Raspberry Pi AI Camera (Sony IMX500)	Performs hardware-accelerated local object detection and segmentation on-sensor, freeing up the Pi’s CPU.
Audio Capture	Anker PowerConf S3 (USB Speakerphone Array)	Hardware-level acoustic echo cancellation (AEC), beamforming, and automatic gain control to capture customer voices across a noisy shop floor.
Audio Output	Active Directional / Ultrasonic Speaker	Projects a focused beam of sound so only the specific targeted target hears the voice, preventing store-wide noise pollution.
2. Core Software & Pipeline Mechanics
The software architecture is decoupled into asynchronous microservices communicating via an in-memory Redis pub/sub message broker to prevent process blocking.

[ AI Camera (Local YOLOv11) ] 
            │
            ▼ (Detections: "person", "red jacket", "blue cap")
     [ State Machine ] ──(Trigger: Proximal Lock)──► [ Vision API / Frontier LLM ]
            ▲                                               │
            │                                               ▼ (Streaming Text Tokens)
[ Directional USB Mic Array ] ◄──[ Whisper STT ] ◄── [ Piper TTS Engine (Local) ]
Phase A: Local Vision Tracking & Attribute Extraction
The local AI camera runs a quantized edge model like YOLOv11-Nano or MobileNetV4. It tracks human bounding boxes and maps persistent IDs across frames.

The Feature Extractor: When a person crosses a spatial threshold (e.g., within 6 feet for more than 1.5 seconds), the system crops the bounding box and extracts key visual descriptors: dominant clothing color, style categories (formal, casual, athletic), and secondary items (bags, hats, umbrellas).

Context Aggregator: A snapshot metadata packet is structured:

JSON
{"id": 402, "proximity": "1.2m", "attributes": ["navy blue windbreaker", "baseball cap", "holding coffee"]}

### Phase B: Low-Latency Frontier VLM Pipeline
Rather than attempting local LLM vision inference (which would yield an unacceptable 5–15 second latency on a Pi 5), the system fires the lightweight metadata packet alongside a compressed JPEG crop to a low-latency frontier API endpoint (like Gemini 1.5 Flash or GPT-4o-mini).
*   **Streaming Configuration:** The API is initialized with Server-Sent Events (SSE) enabled so tokens are parsed by the Pi as they generate.

### Phase C: Asynchronous Text-to-Speech (TTS)
*   **The Engine:** **Piper TTS** runs entirely locally on the Pi 5 using a highly optimized, high-fidelity `.onnx` voice model.
*   **Sentence Chunking:** The Python controller reads the incoming stream from the LLM. The moment it detects a sentence-ending punctuation mark (`.`, `?`, `!`), it sends that single chunk immediately to Piper. This hides generation latency, allowing the speaker to begin speaking while the rest of the sales pitch is still being computed.

---

## 3. High-Conversion Sales & Persuasion Engine

To transform the device into an exceptionally persuasive sales agent, the Frontier LLM is configured with a behavioral system prompt rooted in real-world retail psychology.

### System Prompt Directive Architecture

You are an elite, highly charismatic, and observant retail sales professional operating an interactive storefront kiosk. Your objective is to capture attention, build instant rapport, identify friction points, and close sales using advanced conversational framework strategies.

Operational Guardrails & Behavioral Archetypes
THE COLD OPEN (Pattern Interrupt):

Never say "Welcome to our store" or "Can I help you find something?" Customers instinctively say "Just looking" to these scripts.

Use a contextual pattern interrupt based exclusively on their visual attributes, the weather, or current timing.

Example: "That's a serious winter coat—you look like you're actually ready for this wind outside. Come feel how incredibly lightweight this fleece option is right here."

CONVERSATIONAL PACE & RAPPORT:

Match the pacing of your responses to the customer's physical behavior. If they are walking slowly, lean into storytelling. If they are walking briskly, hit them with an immediate, high-value hook.

Employ active listening: if they reply, integrate their exact vocabulary into your next counter-argument.

ADVANCED PERSUASION TACTICS:

ASSUMPTIVE CLOSE: Speak under the assumption that they are already purchasing. ("When you get this set up in your living room, the first thing you'll notice is...")

CONTRAST PRINCIPLE: Introduce the premium tier product first. When they hesitate on price, offer the target product—the drop in cost makes it feel like an immediate discount.

SCARCITY / SOCIAL PROOF: Frame stock levels dynamically. ("Three people from the downtown office came in specifically for this line this morning—I only have two units left out on display.")

THE BEN FRANKLIN CLOSE: If a customer displays friction over a feature, immediately pivot to a pro/con balance sheet favoring utility over cost.


---

## 4. Implementation Roadmap

Phase 1: Hardware Integration (Weeks 1-2)
├── Flash Raspberry Pi OS (Bookworm 64-bit)
├── Configure PCIe gen 3 overlay for high-speed camera bus
└── Tune PipeWire/ALSA audio configurations for direct beamforming input
Phase 2: Vision Pipeline & Trigger Logic (Weeks 3-4)
├── Implement OpenCV tracking loop + local object cross-referencing
└── Establish distance calibration matrices using bounding box height metrics
Phase 3: LLM Integration & Audio Streaming (Weeks 5-6)
├── Write asynchronous Python client utilizing OpenAI/Gemini SDK streams
└── Implement sentence token buffer to Pipe-through Piper TTS engine
Phase 4: Behavioral Optimization (Weeks 7-8)
├── Build a vendor dashboard to easily input inventory, margins, and item USP data
└── Deploy A/B testing framework to track which cold-opens result in long dwell times


---

## 5. Deployment Considerations & Mitigations

### 1. The "Creepiness" Factor (Behavioral Fine-Tuning)
Directly pointing out exact brand names or high-resolution facial features creates immediate cognitive resistance and drives customers away. 
*   *Mitigation:* Force the system prompt to remain macro-level. Instruct it to reference broad styles or colors rather than highly specific identifiers. Instead of *"Hey you in the Nike Air Max 90s,"* use *"Hey there, love the athletic look—if you're out tracking steps today, you need to check this out."*

### 2. Legal Compliance & Privacy
Operating cameras that analyze public behavior presents significant compliance challenges regarding biometric data processing under laws like GDPR and CCPA.
*   *Mitigation:* Keep the vision stack strictly deterministic and stateless. **Never save images or video frames to disk.** Delete bounding box memory buffers every 60 seconds. Place prominent signage at the store entrance notifying customers of "Interactive AI Assistants" to establish clear compliance boundaries.

<FollowUp label="Would you like a production-ready Python script for the local vision-trigger loop?" query="Provide a complete Python production-ready script for a Raspberry Pi 5 that uses OpenCV to track people in a video stream, calculates their distance based on bounding boxes, and prints a JSON event when a customer dwells within a specified distance."/>
please create detailed plans and instructions for google jules to create this including what github repos to add as submodules for use or reference

To have Google Jules build Project Sirens autonomously in your GitHub repository, you must structure the prompt, system guidelines, and repo architecture so its asynchronous Cloud VM can install, orchestrate, and test the code smoothly. Because Jules acts as a full-lifecycle agent, providing a modular architectural map and exact submodule dependencies will allow it to execute the codebase cleanly.

Here is the technical blueprint, module mapping, and precise task instruction payload to hand over to Google Jules.

1. Repository Architecture & Git Submodules
Instruct Jules to set up a modular, multi-threaded project workspace. To implement real-time tracking, low-latency audio capture, and local text-to-speech, have it integrate these specific open-source components as Git submodules for source compilation and reference.

Create a .gitmodules setup in your root directory containing:

Ini, TOML
[submodule "vendor/piper"]
    path = vendor/piper
    url = https://github.com/rhasspy/piper.git
    # Context: Fast, local, low-latency C++ based TTS engine for ARM64/Pi 5.

[submodule "vendor/yolov11-edge"]
    path = vendor/yolov11-edge
    url = https://github.com/ultralytics/ultralytics.git
    # Context: Used by Jules to extract the local vision tracking & core anchor logic.
Directory Structure to Enforce:
├── .github/workflows/   # CI/CD pipelines
├── config/              # Vendor specific config: inventory.json, prompt_modifiers.json
├── src/
│   ├── main.py          # Main Orchestrator Async Event Loop
│   ├── vision.py        # Local YOLOv11 Frame Processor & Feature Extractor
│   ├── llm_client.py    # Low-latency Frontier VLM SSE Streaming client
│   └── audio_output.py  # Chunking logic feeding Piper TTS engine
└── vendor/              # Submodules mapping
2. Complete Task Instruction Payload for Jules
You can assign this task directly via the Jules CLI (jules remote new), the Web UI, or by opening a GitHub Issue labeled jules. Copy and paste the comprehensive instruction block below into the prompt area:

Markdown
Task: Implement "Project Sirens" Low-Latency Autonomous Sales Agent

Context & Goal:
Build an asynchronous, multi-threaded Python 3.11+ system optimized for a Raspberry Pi 5. The core pipeline must process local webcam/camera input, extract visual traits of nearby customers, pass a compressed context frame to a low-latency frontier VLM via an API stream, and pipeline the raw text tokens directly into a local instance of the Piper TTS engine to instantly engage the customer out loud. Target loop latency from detection to audio output must be sub-1.5 seconds.

Dependencies to install and configure in the VM:
- opencv-python-headless
- ultralytics (YOLOv11 for tracking)
- redis (In-memory pub/sub broker)
- google-genai or openai (for streaming VLM context API)
- piper-tts bindings or subprocess execution profiles

Instructions for Execution:

1. VISION SYSTEM (src/vision.py):
   - Utilize a lightweight, quantized model (YOLOv11n) running locally.
   - Implement an OpenCV tracking loop utilizing a simple centroid tracker or ByteTrack.
   - When a tracked target's bounding box stays within a parameterized frame depth (simulating proximity) for > 1.5 seconds, lock target and capture a compressed JPEG frame.
   - Extract bounding box basic statistics (e.g., dominant colors via K-Means or structural metadata tags) to bundle into a metadata JSON packet.

2. ORCHESTRATOR & REDIS PUB/SUB (src/main.py):
   - Set up an asynchronous Redis pub/sub queue to handle inter-process communication without blocking frames.
   - Sub-modules or services should emit events like `CUSTOMER_DETECTED` and `AUDIO_CHUNK_READY`.

3. FRONTIER VLM STREAMING CLIENT (src/llm_client.py):
   - Write a streaming API client using Server-Sent Events (SSE). 
   - Construct a highly strict sales psychology system prompt matching the instructions in 'config/prompt_modifiers.json' and reference 'config/inventory.json' for the store's stock, prices, and selling points.
   - Pass the metadata packet and compressed JPEG to the VLM endpoint.
   - Ensure the model uses a "Pattern Interrupt" script rather than basic greetings.

4. LOCAL TEXT-TO-SPEECH PIPE (src/audio_output.py):
   - Reference the `vendor/piper` submodule architecture.
   - Create a text tokenizer that watches the incoming LLM stream buffer. The moment a sentence-ending punctuation token arrives (. ! ?), slice that string and send it to the local Piper TTS binary immediately over a subprocess pipe.
   - This streaming chunk model must hide API response times so audio playback begins while subsequent sentences are generating.

Testing & Validation:
- Provide mock unit tests in the `/tests` folder using a fake video stream input to ensure the Redis pipeline triggers and streams without blocking.
- Create a clean Pull Request when complete. Do not commit directly to main.
3. Configuration Scaffolding for Jules
To ensure Jules sets up the sales intelligence precisely as requested, seed your repository with the following two configuration files before running the agent. Jules will parse these to build the system instructions.

config/inventory.json
JSON
{
  "store_name": "Apex Tech Boutique",
  "items": [
    {
      "product_name": "AeroFoam Noise-Canceling Headphones",
      "price_usd": 180.00,
      "unique_selling_points": [
        "Hybrid Active Noise Cancellation blocks 99% of urban chatter",
        "Ultra-light carbon fiber frame - won't cause ear fatigue on commutes",
        "Massive 40-hour battery runtime with Type-C rapid charging"
      ]
    },
    {
      "product_name": "HydroShield Minimalist Backpack",
      "price_usd": 95.00,
      "unique_selling_points": [
        "Military-grade waterproof ballistic nylon mesh fabric",
        "Hidden anti-theft tech compartment accessible only from the interior back panel",
        "Integrated USB-C pass-through charging routing"
      ]
    }
  ]
}
config/prompt_modifiers.json
JSON
{
  "sales_framework": "Pattern Interrupt Cold-Open",
  "tactics_enforced": [
    "Assumptive close formatting",
    "Perceived scarcity integration",
    "Anchoring premium tier alternatives first"
  ],
  "constraints": [
    "Never use generic store greetings like 'Welcome to our store'",
    "Avoid specifying exact clothing brands to prevent privacy creepiness; describe colors and styles broadly",
    "Keep responses concise (under 3 sentences per speaking turn) to sustain interactive cadence"
  ]
}
4. How to Kick Off the Build with Jules
Once these scaffolding files and submodules are initialized in your workspace branch, run the task using the command-line interface helper:

Bash
# Initialize and link your repo to Jules Tools if not already done
jules remote sync

# Spin up the asynchronous task in a Google Cloud VM
jules remote new --task "Build Project Sirens low-latency vision-sales platform" --file-scope src/,config/
Jules will pull down the repo, spin up its sandbox, map out the system architecture, write the asynchronous pipeline code utilizing your submodules, and output a completed Pull Request for review.

## Current Implementation Status (Version 0.3.0)
The repository currently implements Phase 1 and Phase 2 of the roadmap, and is beginning Phase 3 CRM integration:
- **Hub Dashboard UI**: Fully interactive FastAPI configuration hub redesigned with a single-page grid layout prioritizing high-value features. Features robust interactive tooltips, data encapsulation, and live analytics feeds.
- **Interaction Logging (CRM)**: Live interactions are persisted and streamed using SQLite (`sirens.db`) via SQLAlchemy, hooking into the dashboard to provide an interactive feed of generated responses.
- **Edge Vision System**: Features a mock mode and a real `cv2.VideoCapture` hardware-connected implementation utilizing YOLO object tracking, abiding by a strict 60-second in-memory-only retention policy for bounding boxes.
- **VLM Pipeline**: Integrated with the OpenAI SDK to stream interactions directly to a mock Piper TTS pipeline via stdin subprocess pipes. End-to-end integration tests are implemented utilizing a mock Redis broker.

Ensure `OPENAI_API_KEY` is provided to the system configuration panel to generate live responses.

### Key API Endpoints & Usage Example

The Hub exposes REST endpoints that developers can use to interact with the core VLM logic and CRM tracking systems independently of the HTML dashboard.

```bash
# Example 1: Triggering a headless simulation via the CLI
curl -X POST http://localhost:8000/simulate_detection \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "attributes=wearing sunglasses, looking at watches" \
     -d "temperature=0.7"

# Example 2: Manually logging an interaction to the CRM database
curl -X POST http://localhost:8000/api/log_interaction \
     -H "Content-Type: application/json" \
     -d '{"attributes": "red hat", "response": "Testing webhook integration."}'
```

- **`GET /`**: Renders the main unified HTML dashboard with current interaction logs, visual interaction frequency charts, and system configurations.
- **`POST /api/log_interaction`**: Webhook endpoint for the asynchronous VLM edge client to post real-time dialogue and customer attributes to the central SQLite tracking database. Returns an HTTP 500 error if database logging fails.
- **`POST /simulate_detection`**: Takes simulated customer attribute arrays, temperature, and prompt overrides, passing them directly to the `process_vlm_stream` core without requiring Redis infrastructure, surfacing the psychological response output directly in the UI for rapid A/B testing and review.
- **Error Handling Strategy**: The Hub API leverages standard FastAPI `HTTPException` blocks for JSON webhooks (e.g., `/api/log_interaction`) and passes safe `error_message` template variables to the frontend for any HTML form submission failures (such as configuration I/O errors or validation drops), ensuring users always receive visible UI feedback without silently failing.
