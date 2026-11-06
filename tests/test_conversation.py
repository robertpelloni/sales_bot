import asyncio
import json
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from llm_client import (
    generate_sales_response,
    construct_system_prompt,
    chunk_text_stream,
    format_multimodal_user_content,
    process_vlm_stream,
    derive_scarcity_and_urgency
)


def test_derive_scarcity_and_urgency():
    """Verifies that dwell time and spatial proximity scale urgency and generate appropriate scarcity directives."""
    # Critical scarcity: long dwell time (>5s) and intimate proximity
    level, directive = derive_scarcity_and_urgency({
        "dwell_time_s": 5.5,
        "proximity": "1.0m (close)",
        "distance_m": 1.0
    })
    assert level == "CRITICAL_SCARCITY"
    assert "intimate proximity" in directive
    assert "scarcity" in directive

    # High urgency: dwell time >= 3.0s
    level, directive = derive_scarcity_and_urgency({
        "dwell_time_s": 3.8,
        "proximity": "1.8m (mid-range)",
        "distance_m": 1.8
    })
    assert level == "HIGH_URGENCY"
    assert "selling out fast" in directive

    # Moderate urgency: close proximity without extended dwell time
    level, directive = derive_scarcity_and_urgency({
        "dwell_time_s": 1.2,
        "proximity": "1.0m (close)",
        "distance_m": 1.0
    })
    assert level == "MODERATE_URGENCY"

    # Mild urgency: mid-range approach
    level, directive = derive_scarcity_and_urgency({
        "dwell_time_s": 0.5,
        "proximity": "2.0m (mid-range)",
        "distance_m": 2.0
    })
    assert level == "MILD_SCARCITY"


@pytest.mark.asyncio
async def test_scarcity_fallback_in_sales_response():
    """Verifies that fallback responses append scarcity suffixes when urgency is high or critical."""
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]

    # Critical scarcity packet
    critical_packet = {
        "attributes": ["navy blue windbreaker"],
        "dwell_time_s": 6.0,
        "proximity": "1.0m (close)",
        "distance_m": 1.0
    }
    response = await generate_sales_response("Mock prompt", critical_packet)
    assert "winter coat" in response
    assert "only have one or two units left" in response

    # High urgency packet
    high_urgency_packet = {
        "attributes": ["holding coffee"],
        "dwell_time_s": 3.5,
        "proximity": "1.8m (mid-range)",
        "distance_m": 1.8
    }
    response = await generate_sales_response("Mock prompt", high_urgency_packet)
    assert "coffee fuel" in response
    assert "flying off the rack" in response

@pytest.mark.asyncio
async def test_generate_sales_response():
    sys_prompt = "Mock prompt"

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

    # Test athletic / sneakers condition
    customer_packet = {"attributes": ["red sneakers"]}
    response = await generate_sales_response(sys_prompt, customer_packet)
    assert "athletic" in response

    # Test default fallback condition
    customer_packet = {"attributes": ["plain yellow hat"]}
    response = await generate_sales_response(sys_prompt, customer_packet)
    assert "show you something" in response


@pytest.mark.asyncio
async def test_construct_system_prompt():
    inventory = {
        "store_name": "Test Store",
        "items": [{"product_name": "Test Item", "price_usd": 50}],
        "promotions": [{"rule_name": "Summer Promo", "discount_percent": 15}]
    }
    prompt_modifiers = {"sales_framework": "Test Framework", "tactics_enforced": ["Urgency"], "constraints": ["Be polite"]}

    # Without bandit insights
    prompt = construct_system_prompt(inventory, prompt_modifiers)
    assert "Test Store" in prompt
    assert "Test Framework" in prompt
    assert "Summer Promo" in prompt
    assert "Urgency" in prompt
    assert "Be polite" in prompt

    # With bandit insights
    bandit_insights = {
        "recommended_framework": "Challenger Sales Framework",
        "win_rate": 38.5,
        "guidance": "Empirical leader from Bayesian bandit.",
        "confidence_interval": "[28.0% - 50.0%]"
    }
    prompt_with_bandit = construct_system_prompt(inventory, prompt_modifiers, bandit_insights=bandit_insights)
    assert "Challenger Sales Framework" in prompt_with_bandit
    assert "38.5%" in prompt_with_bandit
    assert "Empirical leader from Bayesian bandit." in prompt_with_bandit
    assert "[28.0% - 50.0%]" in prompt_with_bandit


@pytest.mark.asyncio
async def test_sales_response_with_promotions():
    """Verifies that sales response fallback injects matched promotional discounts into opening pitches."""
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]

    customer_packet = {
        "attributes": ["navy blue windbreaker"],
        "dwell_time_s": 2.0,
        "proximity": "1.5m (mid-range)",
        "distance_m": 1.5,
        "matched_promos": [
            {
                "rule_name": "Spring Flash Sale",
                "discount_percent": 25.0,
                "description": "25% off all windbreakers"
            }
        ]
    }

    response = await generate_sales_response("Mock prompt", customer_packet)
    assert "winter coat" in response
    assert "Spring Flash Sale" in response
    assert "25.0% off" in response


def test_chunk_text_stream():
    """Verifies that chunk_text_stream divides streams into sentence-level chunks ending with . ! ?."""
    text = "Hello there! Welcome to the boutique. Check out this coat?"
    chunks = chunk_text_stream(text)
    assert len(chunks) == 3
    assert chunks[0] == "Hello there!"
    assert chunks[1] == "Welcome to the boutique."
    assert chunks[2] == "Check out this coat?"

    # Handling text without trailing punctuation
    trailing_text = "Sentence one. Sentence two without period"
    chunks_trailing = chunk_text_stream(trailing_text)
    assert len(chunks_trailing) == 2
    assert chunks_trailing[0] == "Sentence one."
    assert chunks_trailing[1] == "Sentence two without period"


def test_format_multimodal_user_content():
    """Verifies format_multimodal_user_content constructs image_url when base64 frame is present."""
    # Without image
    packet_no_img = {"attributes": ["red cap"], "proximity": "1.2m"}
    content_no_img = format_multimodal_user_content(packet_no_img)
    assert len(content_no_img) == 1
    assert content_no_img[0]["type"] == "text"
    assert "red cap" in content_no_img[0]["text"]

    # With compressed base64 image
    dummy_b64 = "A" * 150
    packet_with_img = {"attributes": ["blue coat"], "proximity": "close", "frame_data": dummy_b64}
    content_with_img = format_multimodal_user_content(packet_with_img)
    assert len(content_with_img) == 2
    assert content_with_img[0]["type"] == "text"
    assert content_with_img[1]["type"] == "image_url"
    assert "data:image/jpeg;base64,AAA" in content_with_img[1]["image_url"]["url"]


@pytest.mark.asyncio
async def test_multimodal_sales_response_with_api_mock(monkeypatch):
    """Verifies that OpenAI AsyncOpenAI client is called with multimodal user messages when key is present."""
    mock_client = AsyncMock()
    mock_completion = AsyncMock()
    mock_choice = AsyncMock()
    mock_choice.message.content = "Frontier VLM personalized pitch based on your blue coat."
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion

    import llm_client
    monkeypatch.setattr(llm_client, "get_system_config", lambda: ("sk-mock-key-valid", "False"))
    monkeypatch.setattr(llm_client, "AsyncOpenAI", lambda api_key: mock_client)

    packet = {
        "attributes": ["blue coat"],
        "proximity": "1.1m",
        "frame_data": "B" * 120
    }

    resp = await generate_sales_response("Test prompt", packet)
    assert resp == "Frontier VLM personalized pitch based on your blue coat."
    mock_client.chat.completions.create.assert_called_once()


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

    final_response = await process_vlm_stream(packet_json, mock_redis)

    assert "winter coat" in final_response
    assert len(mock_redis.published_messages) > 0
    assert mock_redis.published_messages[0]["channel"] == "AUDIO_CHUNK_READY"
    assert "winter coat" in mock_redis.published_messages[0]["message"]
