import json
import asyncio
import os
import re

async def load_configs():
    inventory = {"store_name": "Unknown", "items": []}
    prompt_modifiers = {"sales_framework": "Generic", "tactics_enforced": [], "constraints": []}

    try:
        if os.path.exists("config/inventory.json"):
            with open("config/inventory.json", "r") as f:
                inventory = json.load(f)
        elif os.path.exists("../config/inventory.json"):
            with open("../config/inventory.json", "r") as f:
                inventory = json.load(f)

        if os.path.exists("config/prompt_modifiers.json"):
            with open("config/prompt_modifiers.json", "r") as f:
                prompt_modifiers = json.load(f)
        elif os.path.exists("../config/prompt_modifiers.json"):
            with open("../config/prompt_modifiers.json", "r") as f:
                prompt_modifiers = json.load(f)
    except Exception as e:
        print(f"Error loading configs: {e}")

    return inventory, prompt_modifiers

def construct_system_prompt(inventory, prompt_modifiers):
    system_prompt = f"You are an elite, highly charismatic retail sales professional operating in {inventory['store_name']}.\n"
    system_prompt += f"Primary Framework: {prompt_modifiers['sales_framework']}\n"
    system_prompt += f"Inventory Available:\n{json.dumps(inventory['items'], indent=2)}\n"

    system_prompt += "Tactics to enforce:\n"
    for tactic in prompt_modifiers.get("tactics_enforced", []):
        system_prompt += f"- {tactic}\n"

    system_prompt += "Constraints:\n"
    for constraint in prompt_modifiers.get("constraints", []):
        system_prompt += f"- {constraint}\n"

    return system_prompt

import os
import httpx
from openai import AsyncOpenAI

def get_system_config():
    import json, os
    api_key = os.getenv("OPENAI_API_KEY")
    use_mock_vision = os.getenv("USE_MOCK_VISION", "True")

    # Try reading from the shared config file the hub drops
    config_path = "config/system_config.json" if os.path.exists("config/system_config.json") else "../config/system_config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                conf = json.load(f)
                api_key = conf.get("OPENAI_API_KEY", api_key)
                use_mock_vision = conf.get("USE_MOCK_VISION", use_mock_vision)
        except Exception:
            pass

    return api_key, use_mock_vision

async def generate_sales_response(sys_prompt, customer_packet):
    """
    Generates the sales pitch based on system prompt and customer context.
    If an OpenAI API key is configured, uses the real API. Otherwise, falls back to a mock response.
    """
    api_key, _ = get_system_config()

    # Allow packet overrides
    temperature = customer_packet.get("temperature", 0.8)
    override_prompt = customer_packet.get("system_prompt_override", "").strip()
    if override_prompt:
        sys_prompt = override_prompt

    if api_key and api_key.strip():
        client = AsyncOpenAI(api_key=api_key)

        attributes_str = ", ".join(customer_packet.get("attributes", []))
        user_message = f"Customer detected with these attributes: {attributes_str}."

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=150,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM API Error: {e}")
            # Fall through to mock if API fails
            pass

    # Fallback mock logic
    attributes = customer_packet.get("attributes", [])
    if any("coat" in attr.lower() or "jacket" in attr.lower() or "windbreaker" in attr.lower() for attr in attributes):
        return "That's a serious winter coat. You look like you're actually ready for this wind outside! Come feel how incredibly lightweight this fleece option is right here."
    elif any("coffee" in attr.lower() for attr in attributes):
        return "Hey, looks like you've got your coffee fuel for the day! While you're at it, check out our new arrivals."
    else:
        return "Hey there! If you have a minute, I'd love to show you something that just arrived in store."

async def process_vlm_stream(data: str, redis_client=None):
    """
    Mock streaming API client using SSE-like behavior.
    """
    try:
        packet = json.loads(data)
        inventory, prompt_modifiers = await load_configs()
        sys_prompt = construct_system_prompt(inventory, prompt_modifiers)

        # print(f"VLM Streamer initialized with prompt framework: {prompt_modifiers['sales_framework']}")

        simulated_response = await generate_sales_response(sys_prompt, packet)

        buffer = ""
        tokens = simulated_response.split(" ")
        for token in tokens:
            await asyncio.sleep(0.01) # Simulate API latency
            buffer += token + " "

            if re.search(r'[.!?]', buffer):
                chunk_to_send = buffer.strip()
                # print(f"VLM Chunk Complete: {chunk_to_send}")
                if redis_client:
                    await redis_client.publish("AUDIO_CHUNK_READY", chunk_to_send)
                buffer = ""

        if buffer.strip():
            if redis_client:
                await redis_client.publish("AUDIO_CHUNK_READY", buffer.strip())

        # Log interaction to Hub API asynchronously without blocking the response return
        async def log_to_hub():
            try:
                # Wait briefly for any TTS latency metrics to hit Redis
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
                import base64
                auth_str = f"{os.getenv('ADMIN_USER', 'admin')}:{os.getenv('ADMIN_PASS', 'password')}"
                b64_auth = base64.b64encode(auth_str.encode()).decode()

                async with httpx.AsyncClient(timeout=3.0) as http_client:
                    # Use localhost if running locally, or `hub` if inside docker network
                    hub_url = os.getenv("HUB_URL", "http://localhost:8000")
                    await http_client.post(
                        f"{hub_url}/api/log_interaction",
                        headers={"Authorization": f"Basic {b64_auth}"},
                        json={
                            "attributes": attributes_str,
                            "response": simulated_response,
                            "sales_framework": prompt_modifiers.get('sales_framework', 'Unknown'),
                            "tts_latency_ms": latency_ms
                        }
                    )
            except Exception as e:
                print(f"Failed to log interaction to Hub: {e}")

        # Schedule the logging task to run in the background
        asyncio.create_task(log_to_hub())

        return simulated_response

    except Exception as e:
        print(f"VLM stream error: {e}")
        return str(e)
