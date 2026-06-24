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
If the customer replies, match their pacing and use the Assumptive Close or Ben Franklin Close if they show friction over features or price.
"""

async def fetch_session_history(track_id):
    history_json = await r.get(f"session:{track_id}")
    if history_json:
        return json.loads(history_json.decode('utf-8'))
    return []

async def save_session_history(track_id, history):
    # Set an expiration of 5 minutes for session history
    await r.setex(f"session:{track_id}", 300, json.dumps(history))

async def handle_llm_stream(track_id, messages):
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True,
            max_tokens=150
        )

        buffer = ""
        full_response = ""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                text_chunk = chunk.choices[0].delta.content
                buffer += text_chunk
                full_response += text_chunk

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

        return full_response

    except Exception as e:
        print(f"[LLM Client] Error generating response: {e}")
        return ""

async def handle_events():
    pubsub = r.pubsub()
    await pubsub.subscribe('CUSTOMER_DETECTED', 'CUSTOMER_REPLY')
    print("LLM Client listening for detections and replies...")

    async for message in pubsub.listen():
        if message['type'] == 'message':
            channel = message['channel'].decode('utf-8')
            data = json.loads(message['data'].decode('utf-8'))

            if channel == 'CUSTOMER_DETECTED':
                metadata = data['metadata']
                track_id = metadata['id']
                image_b64 = data['image_b64']

                print(f"[LLM Client] Received detection for ID {track_id}")

                # Fetch history to ensure we don't cold-open someone we're already talking to
                history = await fetch_session_history(track_id)
                if len(history) > 0:
                    print(f"[LLM Client] ID {track_id} already has an active session. Ignoring re-trigger.")
                    continue

                # Construct user message with image and metadata for a Cold Open
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

                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ]

                full_response = await handle_llm_stream(track_id, messages)

                # Save state
                messages.append({"role": "assistant", "content": full_response})
                await save_session_history(track_id, messages)

            elif channel == 'CUSTOMER_REPLY':
                track_id = data['id']
                customer_text = data['text']

                print(f"[LLM Client] Received reply from ID {track_id}: {customer_text}")

                history = await fetch_session_history(track_id)
                if not history:
                    # Fallback if history expired but they replied
                    history = [{"role": "system", "content": SYSTEM_PROMPT}]

                # Append customer reply
                history.append({"role": "user", "content": customer_text})

                # Stream response
                full_response = await handle_llm_stream(track_id, history)

                # Save state
                history.append({"role": "assistant", "content": full_response})
                await save_session_history(track_id, history)

if __name__ == "__main__":
    asyncio.run(handle_events())
