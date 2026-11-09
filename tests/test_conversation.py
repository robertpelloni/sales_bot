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
    derive_scarcity_and_urgency,
    derive_customer_persona
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
    assert "SonicStride" in response

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


def test_derive_customer_persona():
    """Verifies that sensory features map accurately into behavioral retail customer personas."""
    # Athletic persona
    p1 = derive_customer_persona({"attributes": ["athletic shorts", "running sneakers"]})
    assert p1["persona"] == "Athletic / Commuter"
    assert "Footwear" in p1["recommended_category"]

    # Weather traveler persona
    p2 = derive_customer_persona({"attributes": ["rain jacket", "hoodie"]})
    assert p2["persona"] == "Weather-Conscious / Urban Traveler"
    assert "Outerwear" in p2["recommended_category"]

    # Lifestyle browser
    p3 = derive_customer_persona({"attributes": ["carrying coffee", "tote bag"]})
    assert p3["persona"] == "Lifestyle / Urban Browser"

    # Deep evaluator (high dwell time)
    p4 = derive_customer_persona({"attributes": ["formal watch"], "dwell_time_s": 8.5})
    assert p4["persona"] == "Deep Evaluator / Quality Seeker"

    # Default spontaneous
    p5 = derive_customer_persona({"attributes": ["plain shirt"], "dwell_time_s": 1.0})
    assert p5["persona"] == "Spontaneous Shopper"


@pytest.mark.asyncio
async def test_persona_variations_with_promotions():
    """
    Verifies that various customer personas receive tailored opening pitches
    combined with dynamically triggered store promotions and scarcity hooks.
    """
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]

    # 1. Athletic persona with dwell discount
    athletic_packet = {
        "attributes": ["runner sneakers", "athletic socks"],
        "dwell_time_s": 32.0,
        "proximity": "1.1m (close)",
        "distance_m": 1.1,
        "matched_promos": [{"rule_name": "Dwell Engagement Bundle", "discount_percent": 20.0}]
    }
    p_athletic = await generate_sales_response("Mock prompt", athletic_packet)
    assert "SonicStride" in p_athletic
    assert "Dwell Engagement Bundle" in p_athletic
    assert "20.0% off" in p_athletic
    assert "units left" in p_athletic  # Critical scarcity (dwell >= 5s and close)

    # 2. Weather traveler persona with outerwear promo
    weather_packet = {
        "attributes": ["heavy winter coat", "windbreaker"],
        "dwell_time_s": 3.5,
        "proximity": "1.8m (mid-range)",
        "distance_m": 1.8,
        "matched_promos": [{"rule_name": "Rainy Day Flash Sale", "discount_percent": 15.0}]
    }
    p_weather = await generate_sales_response("Mock prompt", weather_packet)
    assert "winter coat" in p_weather
    assert "Rainy Day Flash Sale" in p_weather
    assert "15.0% off" in p_weather
    assert "flying off the rack" in p_weather  # High urgency (dwell >= 3s)

    # 3. Lifestyle browser with coffee
    lifestyle_packet = {
        "attributes": ["iced coffee cup", "tote bag"],
        "dwell_time_s": 1.0,
        "proximity": "1.5m (mid-range)",
        "distance_m": 1.5,
        "matched_promos": []
    }
    p_lifestyle = await generate_sales_response("Mock prompt", lifestyle_packet)
    assert "coffee fuel" in p_lifestyle
    assert "featured accessories" in p_lifestyle

    # 4. Deep Evaluator / Quality Seeker with high dwell time
    quality_packet = {
        "attributes": ["formal business shoes"],
        "dwell_time_s": 7.0,
        "proximity": "2.0m (mid-range)",
        "distance_m": 2.0,
        "matched_promos": [{"rule_name": "VIP Quality Incentive", "discount_percent": 10.0}]
    }
    p_quality = await generate_sales_response("Mock prompt", quality_packet)
    assert "craftsmanship" in p_quality
    assert "hydrophobic nanopore weave" in p_quality
    assert "VIP Quality Incentive" in p_quality


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
