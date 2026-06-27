import os
import asyncio
import json
import base64
import unittest
from unittest.mock import patch
import redis.asyncio as redis
from src.llm_client import handle_events
from src.audio_output import process_audio_chunks

class TestConversationalFlow(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.redis = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379, db=0)

    async def asyncTearDown(self):
        # Clean up keys created during tests
        await self.redis.delete("session:999")
        await self.redis.aclose()

    @patch('src.llm_client.client.chat.completions.create')
    async def test_multiturn_conversational_flow(self, mock_create):
        # Mock the OpenAI streaming response for the two turns
        class AsyncMockStreamColdOpen:
            def __init__(self):
                self.items = ["Cold ", "open ", "pitch."]
            async def __aiter__(self):
                for item in self.items:
                    class MockDelta:
                        def __init__(self, content):
                            self.content = content
                    class MockChoice:
                        def __init__(self, content):
                            self.delta = MockDelta(content)
                    class MockChunk:
                        def __init__(self, content):
                            self.choices = [MockChoice(content)]
                    yield MockChunk(item)
            def __await__(self):
                async def return_self():
                    return self
                return return_self().__await__()

        class AsyncMockStreamReply:
            def __init__(self):
                self.items = ["Handling ", "the ", "objection."]
            async def __aiter__(self):
                for item in self.items:
                    class MockDelta:
                        def __init__(self, content):
                            self.content = content
                    class MockChoice:
                        def __init__(self, content):
                            self.delta = MockDelta(content)
                    class MockChunk:
                        def __init__(self, content):
                            self.choices = [MockChoice(content)]
                    yield MockChunk(item)
            def __await__(self):
                async def return_self():
                    return self
                return return_self().__await__()

        # Mock side_effect to return different streams on subsequent calls
        mock_create.side_effect = [AsyncMockStreamColdOpen(), AsyncMockStreamReply()]

        # Start listeners in the background
        llm_task = asyncio.create_task(handle_events())

        # Allow them to subscribe
        await asyncio.sleep(0.1)

        # Subscribe to audio to verify output
        pubsub = self.redis.pubsub()
        await pubsub.subscribe('AUDIO_CHUNK_READY')

        # 1. Publish mock detection (Cold Open)
        mock_img = base64.b64encode(b"mock_image_data").decode('utf-8')
        payload = {
            "metadata": {"id": 999, "attributes": ["mock test attributes"]},
            "image_b64": mock_img
        }
        await self.redis.publish('CUSTOMER_DETECTED', json.dumps(payload))

        # Wait for processing
        await asyncio.sleep(0.5)

        # Read the cold open output
        received_chunks = []
        timeout = 2.0
        start_time = asyncio.get_event_loop().time()

        while len(received_chunks) < 1 and (asyncio.get_event_loop().time() - start_time) < timeout:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                received_chunks.append(message['data'].decode('utf-8'))
            else:
                await asyncio.sleep(0.05)

        self.assertIn("Cold open pitch.", received_chunks)

        # Verify session state
        history = await self.redis.get("session:999")
        self.assertIsNotNone(history)
        history_list = json.loads(history.decode('utf-8'))
        self.assertEqual(len(history_list), 3) # System, User (image), Assistant

        # 2. Publish mock reply
        reply_payload = {
            "id": 999,
            "text": "I don't know, it looks expensive."
        }
        await self.redis.publish('CUSTOMER_REPLY', json.dumps(reply_payload))

        await asyncio.sleep(0.5)

        # Read the objection handler output
        start_time = asyncio.get_event_loop().time()
        while len(received_chunks) < 2 and (asyncio.get_event_loop().time() - start_time) < timeout:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                received_chunks.append(message['data'].decode('utf-8'))
            else:
                await asyncio.sleep(0.05)

        self.assertIn("Handling the objection.", received_chunks)

        # Verify updated session state
        history = await self.redis.get("session:999")
        history_list = json.loads(history.decode('utf-8'))
        self.assertEqual(len(history_list), 5) # System, User, Assistant, User (reply), Assistant (objection)

        llm_task.cancel()
        try:
            await llm_task
        except asyncio.CancelledError:
            pass

if __name__ == '__main__':
    unittest.main()