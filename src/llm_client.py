import asyncio
import json
import os
import re
from openai import AsyncOpenAI
import redis.asyncio as redis

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Init OpenAI client (Requires OPENAI_API_KEY environment variable)
client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", "mock-key"))

def load_config():
    with open('config/inventory.json', 'r') as f:
        inventory = json.load(f)
    with open('config/prompt_modifiers.json', 'r') as f:
        modifiers = json.load(f)
    return inventory, modifiers

INVENTORY, MODIFIERS = load_config()

SYSTEM_PROMPT = f"""
You are an elite, highly charismatic, and observant retail sales professional operating an interactive storefront kiosk.
Your objective is to capture attention, build instant rapport, identify friction points, and close sales using advanced conversational framework strategies.

Store Name: {INVENTORY['store_name']}
Inventory:
{json.dumps(INVENTORY['items'], indent=2)}

Tactics to enforce: {', '.join(MODIFIERS['tactics_enforced'])}
Constraints: {', '.join(MODIFIERS['constraints'])}

IMPORTANT: Match your greeting to the visual attributes provided in the user's message using a 'Pattern Interrupt Cold-Open'. Do not use generic store greetings.
"""

async def handle_detection():
    pubsub = r.pubsub()
    await pubsub.subscribe('CUSTOMER_DETECTED')
    print("LLM Client listening for detections...")

    async for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'].decode('utf-8'))
            metadata = data['metadata']
            image_b64 = data['image_b64']

            print(f"[LLM Client] Received detection for ID {metadata['id']}")

            # Construct user message with image and metadata
            user_content = [
                {
                    "type": "text",
                    "text": f"Customer detected with attributes: {', '.join(metadata['attributes'])}. Give a brief cold open pitch."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}"
                    }
                }
            ]

            # Streaming LLM response
            try:
                # Using GPT-4o-mini as a low-latency frontier VLM
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    stream=True,
                    max_tokens=150
                )

                buffer = ""
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        text_chunk = chunk.choices[0].delta.content
                        buffer += text_chunk

                        # Check for sentence-ending punctuation
                        match = re.search(r'([.!?])(\s+.*)?$', buffer)
                        if match and not buffer.endswith(('.', '!', '?')):
                            # End of sentence found, split it correctly
                            split_index = match.start(1) + 1
                            sentence = buffer[:split_index].strip()
                            buffer = buffer[split_index:].lstrip()
                            await r.publish('AUDIO_CHUNK_READY', sentence)
                        elif buffer.endswith(('.', '!', '?')):
                            await r.publish('AUDIO_CHUNK_READY', buffer.strip())
                            buffer = ""

                # Flush remaining buffer
                if buffer.strip():
                    await r.publish('AUDIO_CHUNK_READY', buffer.strip())

            except Exception as e:
                print(f"[LLM Client] Error generating response: {e}")

if __name__ == "__main__":
    asyncio.run(handle_detection())