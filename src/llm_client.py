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
from openai import AsyncOpenAI

async def generate_sales_response(sys_prompt, customer_packet):
    """
    Generates the sales pitch based on system prompt and customer context.
    If an OpenAI API key is configured, uses the real API. Otherwise, falls back to a mock response.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
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
                temperature=0.8
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

        print(f"VLM Streamer initialized with prompt framework: {prompt_modifiers['sales_framework']}")

        simulated_response = await generate_sales_response(sys_prompt, packet)

        buffer = ""
        tokens = simulated_response.split(" ")
        for token in tokens:
            await asyncio.sleep(0.01) # Simulate API latency
            buffer += token + " "

            if re.search(r'[.!?]', buffer):
                chunk_to_send = buffer.strip()
                print(f"VLM Chunk Complete: {chunk_to_send}")
                if redis_client:
                    await redis_client.publish("AUDIO_CHUNK_READY", chunk_to_send)
                buffer = ""

        if buffer.strip():
            if redis_client:
                await redis_client.publish("AUDIO_CHUNK_READY", buffer.strip())

        return simulated_response

    except Exception as e:
        print(f"VLM stream error: {e}")
        return str(e)
