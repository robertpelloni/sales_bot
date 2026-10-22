# sales_bot — "Project Sirens" (design document only)

**This repository contains no code.** It is a single design document: the
original prompt asking for a plan, the detailed plan that came back, and
build instructions written for Google Jules. Nothing here has been
implemented, and there is nothing to build or run.

## The design

Project Sirens is a proposed shop-floor sales agent: an embedded smart
speaker/camera unit that spots passers-by with computer vision, greets them
based on broad visual attributes (clothing color/style, carried items), and
tries to talk them into a purchase using a frontier LLM configured with
retail sales psychology.

Proposed architecture (edge/cloud split, target <1.5 s from detection to
spoken greeting):

- **Hardware** — Raspberry Pi 5 (8 GB), Raspberry Pi AI Camera (Sony IMX500,
  on-sensor detection), USB speakerphone array for AEC/beamforming, and a
  directional/ultrasonic speaker so only the targeted customer hears it.
- **Vision (local)** — YOLOv11-nano / MobileNet-class tracking with a
  proximity + dwell trigger (>1.5 s within ~6 ft); emits a metadata packet
  (attributes, proximity) plus a compressed JPEG crop. Stateless by design:
  no frames saved, buffers flushed every 60 s.
- **Conversation (cloud)** — the packet goes to a streaming frontier VLM API
  (Gemini Flash / GPT-4o-mini class); tokens stream back over SSE.
- **Speech (local)** — Piper TTS on the Pi, fed sentence-by-sentence as the
  LLM stream produces sentence-ending punctuation, to hide generation
  latency.
- **Coordination** — asynchronous Python services over a Redis pub/sub bus;
  proposed layout `src/vision.py`, `src/llm_client.py`,
  `src/audio_output.py`, `src/main.py`, with `vendor/` submodules for Piper
  and Ultralytics.
- **Sales engine** — a system prompt built on pattern-interrupt cold opens
  (no "welcome to our store"), pacing matched to the customer, assumptive
  close, contrast/anchoring, scarcity/social proof, and a Ben Franklin
  close; constrained to macro-level observations (colors/styles, never
  brands or facial identifiers) to limit the creepiness factor. Vendor
  input via `config/inventory.json` and `config/prompt_modifiers.json`
  (examples included in the document).

The document also includes an 8-week implementation roadmap, privacy/legal
mitigations (GDPR/CCPA, entrance signage), and a complete task payload +
kickoff commands for handing the build to Google Jules.

## Status

Unimplemented plan, written 2026-06-23 (two commits, both the document).
If the build ever happens, it will supersede this file; until then this repo
is the spec, and the spec is all there is.
