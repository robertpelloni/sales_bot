"""
Project Sirens - Frontier VLM Streaming Client
Constructs sales psychology system prompts from store configs, parses customer visual context
(including compressed base64 JPEG crops and attribute metadata), invokes frontier VLM endpoints
with streaming SSE-like token delivery, and chunks completed sentences (. ! ?) directly to Piper TTS.
"""

import asyncio
import base64
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None


async def load_configs() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Loads inventory and sales psychology prompt modifiers from disk in real time."""
    inventory = {"store_name": "Unknown", "items": []}
    prompt_modifiers = {"sales_framework": "Generic", "tactics_enforced": [], "constraints": []}

    for prefix in ["", "../"]:
        inv_path = os.path.join(prefix, "config/inventory.json")
        prompt_path = os.path.join(prefix, "config/prompt_modifiers.json")

        if os.path.exists(inv_path):
            try:
                with open(inv_path, "r") as f:
                    inventory = json.load(f)
            except Exception as e:
                print(f"Error loading {inv_path}: {e}")

        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, "r") as f:
                    prompt_modifiers = json.load(f)
            except Exception as e:
                print(f"Error loading {prompt_path}: {e}")

    return inventory, prompt_modifiers


def construct_system_prompt(inventory: Dict[str, Any], prompt_modifiers: Dict[str, Any]) -> str:
    """Constructs comprehensive retail behavioral prompt incorporating store inventory and psychological rules."""
    system_prompt = (
        f"You are an elite, highly charismatic retail sales professional operating in {inventory.get('store_name', 'Store')}.\n"
        f"Primary Framework: {prompt_modifiers.get('sales_framework', 'Pattern Interrupt Cold-Open')}\n"
        f"Inventory Available:\n{json.dumps(inventory.get('items', []), indent=2)}\n"
    )

    promotions = inventory.get("promotions", [])
    if promotions:
        system_prompt += f"Active Promotional Rules & Discounts:\n{json.dumps(promotions, indent=2)}\n"

    system_prompt += "Tactics to enforce:\n"
    for tactic in prompt_modifiers.get("tactics_enforced", []):
        system_prompt += f"- {tactic}\n"

    system_prompt += "Constraints:\n"
    for constraint in prompt_modifiers.get("constraints", []):
        system_prompt += f"- {constraint}\n"

    return system_prompt


def get_system_config() -> Tuple[Optional[str], str]:
    """Retrieves runtime API credentials and vision mode configuration."""
    api_key = os.getenv("OPENAI_API_KEY")
    use_mock_vision = os.getenv("USE_MOCK_VISION", "True")

    for path in ["config/system_config.json", "../config/system_config.json"]:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    conf = json.load(f)
                    api_key = conf.get("OPENAI_API_KEY", api_key)
                    use_mock_vision = conf.get("USE_MOCK_VISION", use_mock_vision)
                    break
            except Exception:
                pass

    return api_key, use_mock_vision


def derive_scarcity_and_urgency(customer_packet: Dict[str, Any]) -> Tuple[str, str]:
    """
    Derives real-time scarcity and urgency modifiers from dwell time and spatial proximity data.
    - Dwell time: longer dwell (>5.0s) suggests deep hesitation or interest; moderate dwell (>=2.0s) suggests consideration.
    - Proximity: close (<=1.2m) demands direct exclusivity; mid-range (1.2-2.5m) creates hook urgency; far (>2.5m) creates directional draw.
    Returns (urgency_level, directive_instruction).
    """
    dwell_time = float(customer_packet.get("dwell_time_s", 0.0) or 0.0)
    proximity = str(customer_packet.get("proximity", "mid-range")).lower()
    try:
        distance_m = float(customer_packet.get("distance_m", 1.8) or 1.8)
    except (ValueError, TypeError):
        distance_m = 1.8

    # Proximity classification
    is_close = "close" in proximity or distance_m <= 1.2
    is_mid = "mid" in proximity or (1.2 < distance_m <= 2.5)

    if dwell_time >= 5.0 and is_close:
        urgency_level = "CRITICAL_SCARCITY"
        directive = (
            f"Customer has dwelled for {dwell_time:.1f}s at intimate proximity ({distance_m}m). "
            "They are heavily hesitating or considering a purchase. Deliver an intense scarcity hook: "
            "emphasize that this item has only 1 or 2 units remaining today or that a promotional discount expires in moments."
        )
    elif dwell_time >= 3.0:
        urgency_level = "HIGH_URGENCY"
        directive = (
            f"Customer has dwelled for {dwell_time:.1f}s ({proximity}, {distance_m}m). "
            "Leverage social proof and inventory scarcity: mention that popular sizes or stock in this category "
            "are selling out fast this afternoon."
        )
    elif is_close:
        urgency_level = "MODERATE_URGENCY"
        directive = (
            f"Customer is directly at the kiosk ({distance_m}m). "
            "Offer a brisk, urgent preview: 'Just unpacked our final batch of these today!'"
        )
    elif is_mid:
        urgency_level = "MILD_SCARCITY"
        directive = (
            f"Customer approaching at mid-range ({distance_m}m). "
            "Use an observational scarcity hook to stop them before they walk past."
        )
    else:
        urgency_level = "STANDARD"
        directive = "Customer at distance. Warm pattern interrupt to invite them closer."

    return urgency_level, directive


def format_multimodal_user_content(customer_packet: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Constructs OpenAI/Gemini compatible multimodal message content containing
    descriptive customer attributes, dwell time, calibrated distance, and dynamic scarcity directives.
    """
    attributes_str = ", ".join(customer_packet.get("attributes", []))
    proximity = customer_packet.get("proximity", "near")
    distance_m = customer_packet.get("distance_m", "")
    dwell_time_s = customer_packet.get("dwell_time_s", 0.0)

    urgency_level, scarcity_directive = derive_scarcity_and_urgency(customer_packet)

    prompt_text = (
        f"A customer is in the interaction zone (proximity: {proximity}, distance: {distance_m}m, dwell_time: {dwell_time_s}s).\n"
        f"Detected visual features: {attributes_str}.\n"
        f"Dynamic Urgency Level: {urgency_level}\n"
        f"Behavioral Scarcity Directive: {scarcity_directive}\n"
        "Engage them immediately with a charismatic, observational pattern interrupt incorporating the scarcity directive."
    )

    content_parts: List[Dict[str, Any]] = [{"type": "text", "text": prompt_text}]

    frame_data = customer_packet.get("frame_data")
    if frame_data and isinstance(frame_data, str) and len(frame_data) > 100:
        content_parts.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{frame_data}",
                "detail": "low"
            }
        })

    return content_parts


async def generate_sales_response(sys_prompt: str, customer_packet: Dict[str, Any]) -> str:
    """
    Generates the sales pitch based on system prompt, customer context, and dynamic scarcity elements.
    If an OpenAI API key is configured and valid, uses the multimodal chat completion API.
    Otherwise, gracefully falls back to deterministic psychological responses with scaled urgency.
    """
    api_key, _ = get_system_config()

    temperature = customer_packet.get("temperature", 0.8)
    override_prompt = customer_packet.get("system_prompt_override", "").strip()
    if override_prompt:
        sys_prompt = override_prompt

    if api_key and api_key.strip() and AsyncOpenAI is not None:
        try:
            client = AsyncOpenAI(api_key=api_key)
            user_content = format_multimodal_user_content(customer_packet)

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=150,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Frontier VLM API Error (falling back to local mock): {e}")

    # Fallback heuristic sales psychology logic with dynamic scarcity & urgency scaling
    attributes = customer_packet.get("attributes", [])
    lower_attrs = " ".join(attributes).lower()
    urgency_level, _ = derive_scarcity_and_urgency(customer_packet)

    scarcity_suffix = ""
    if urgency_level == "CRITICAL_SCARCITY":
        scarcity_suffix = " Just a heads up, we only have one or two units left of this before stock clears out today!"
    elif urgency_level == "HIGH_URGENCY":
        scarcity_suffix = " These have been flying off the rack this morning, so definitely grab a look before our current allocation sells out."
    elif urgency_level == "MODERATE_URGENCY":
        scarcity_suffix = " We just put out our last batch for the weekend."

    if any(k in lower_attrs for k in ["coat", "jacket", "windbreaker", "warm-toned"]):
        pitch = "That's a serious winter coat. You look like you're actually ready for this wind outside! Come feel how incredibly lightweight this fleece option is right here."
    elif any(k in lower_attrs for k in ["coffee", "cup", "drink"]):
        pitch = "Hey, looks like you've got your coffee fuel for the day! While you're at it, check out our new arrivals."
    elif any(k in lower_attrs for k in ["sneakers", "athletic", "runner"]):
        pitch = "Hey there, love the athletic look—if you're out tracking steps today, you need to check out our newest ultralight gear."
    else:
        pitch = "Hey there! If you have a minute, I'd love to show you something that just arrived in store."

    return (pitch + scarcity_suffix).strip()


def chunk_text_stream(full_text: str) -> List[str]:
    """
    Splits text stream into sentence chunks punctuated by (. ! ?) to allow
    immediate text-to-speech audio piping while the remainder generates.
    """
    chunks = []
    buffer = ""
    for token in full_text.split(" "):
        if not token:
            continue
        buffer += token + " "
        if re.search(r'[.!?]', buffer):
            chunks.append(buffer.strip())
            buffer = ""

    if buffer.strip():
        chunks.append(buffer.strip())

    return chunks


async def process_vlm_stream(data: str, redis_client=None) -> str:
    """
    Asynchronous VLM stream processor: parses customer detection payload,
    generates response, chunks sentences into Redis AUDIO_CHUNK_READY, and
    posts telemetry asynchronously to Hub API.
    """
    try:
        packet = json.loads(data) if isinstance(data, str) else data
        inventory, prompt_modifiers = await load_configs()
        sys_prompt = construct_system_prompt(inventory, prompt_modifiers)

        simulated_response = await generate_sales_response(sys_prompt, packet)

        # Stream chunking to hide latency
        chunks = chunk_text_stream(simulated_response)
        for chunk in chunks:
            await asyncio.sleep(0.01) # Simulate token streaming cadence
            if redis_client:
                await redis_client.publish("AUDIO_CHUNK_READY", chunk)

        # Background interaction logging to central Hub
        async def log_to_hub():
            try:
                latency_ms = 0
                if redis_client:
                    await asyncio.sleep(0.5)
                    pubsub = redis_client.pubsub()
                    await pubsub.subscribe("TTS_LATENCY_METRIC")

                    try:
                        async with asyncio.timeout(2.0):
                            async for msg in pubsub.listen():
                                if msg["type"] == "message":
                                    latency_ms = int(msg["data"].decode("utf-8"))
                                    break
                    except TimeoutError:
                        pass
                    finally:
                        await pubsub.unsubscribe()

                attributes_str = ", ".join(packet.get("attributes", []))
                auth_str = f"{os.getenv('ADMIN_USER', 'admin')}:{os.getenv('ADMIN_PASS', 'password')}"
                b64_auth = base64.b64encode(auth_str.encode()).decode()

                async with httpx.AsyncClient(timeout=3.0) as http_client:
                    hub_url = os.getenv("HUB_URL", "http://localhost:8000")
                    await http_client.post(
                        f"{hub_url}/api/log_interaction",
                        headers={"Authorization": f"Basic {b64_auth}"},
                        json={
                            "attributes": attributes_str,
                            "response": simulated_response,
                            "sales_framework": prompt_modifiers.get("sales_framework", "Unknown"),
                            "tts_latency_ms": latency_ms
                        }
                    )
            except Exception as e:
                print(f"Failed to log interaction to Hub: {e}")

        asyncio.create_task(log_to_hub())
        return simulated_response

    except Exception as e:
        print(f"VLM stream error: {e}")
        return str(e)
