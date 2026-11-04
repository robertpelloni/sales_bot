import asyncio
import json
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from llm_client import generate_sales_response, construct_system_prompt

@pytest.mark.asyncio
async def test_generate_sales_response():
    sys_prompt = "Mock prompt"

    # Ensure OPENAI_API_KEY is not set for mock tests
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]

    # Test coat condition
    customer_packet = {"attributes": ["navy blue windbreaker"]}
    response = await generate_sales_response(sys_prompt, customer_packet)
    assert "winter coat" in response

    # Test coffee condition
    customer_packet = {"attributes": ["holding coffee"]}
    response = await generate_sales_response(sys_prompt, customer_packet)
    assert "coffee fuel" in response

    # Test default condition
    customer_packet = {"attributes": ["red shoes"]}
    response = await generate_sales_response(sys_prompt, customer_packet)
    assert "show you something" in response

@pytest.mark.asyncio
async def test_construct_system_prompt():
    inventory = {"store_name": "Test Store", "items": []}
    prompt_modifiers = {"sales_framework": "Test Framework", "tactics_enforced": [], "constraints": []}

    prompt = construct_system_prompt(inventory, prompt_modifiers)
    assert "Test Store" in prompt
    assert "Test Framework" in prompt

class MockPubSub:
    async def subscribe(self, *channels):
        pass

    async def unsubscribe(self, *channels):
        pass

    async def listen(self):
        yield {"type": "message", "channel": b"TTS_LATENCY_METRIC", "data": b"150"}

class MockRedis:
    def __init__(self):
        self.published_messages = []

    async def publish(self, channel, message):
        self.published_messages.append({"channel": channel, "message": message})

    def pubsub(self):
        return MockPubSub()

@pytest.mark.asyncio
async def test_end_to_end_conversation_flow():
    from llm_client import process_vlm_stream

    # Setup mock environment
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["USE_MOCK_VISION"] = "True"

    mock_redis = MockRedis()
    mock_packet = {
        "id": 1,
        "proximity": "1.0m",
        "attributes": ["navy blue windbreaker"],
        "frame_data": "",
        "system_prompt_override": "",
        "temperature": 0.8
    }

    packet_json = json.dumps(mock_packet)

    # Process the stream
    final_response = await process_vlm_stream(packet_json, mock_redis)

    # Verify the LLM returned our mock expected text for the windbreaker attribute
    assert "winter coat" in final_response

    # Verify the chunker correctly broke down the sentences and sent them to Redis
    assert len(mock_redis.published_messages) > 0
    assert mock_redis.published_messages[0]["channel"] == "AUDIO_CHUNK_READY"
    assert "winter coat" in mock_redis.published_messages[0]["message"]
