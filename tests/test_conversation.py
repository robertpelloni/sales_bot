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
