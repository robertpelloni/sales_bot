import os
import asyncio
import json
import base64
import unittest
from unittest.mock import patch, MagicMock
import redis.asyncio as redis
from src.llm_client import handle_events
from src.audio_output import process_audio_chunks

class TestPipeline(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.redis = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379, db=0)

    async def asyncTearDown(self):
        # Clean up
        await self.redis.close()

    @patch('src.llm_client.client.chat.completions.create')
    async def test_end_to_end_pipeline_mock(self, mock_create):
        # Mock the OpenAI streaming response
        class AsyncMockStream:
            def __init__(self):
                self.items = [
                    "Hey there! ",
                    "Nice jacket. ",
                    "Come look at this."
                ]

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

            # Awaitable so await client.chat.completions.create works
            def __await__(self):
                async def return_self():
                    return self
                return return_self().__await__()

        mock_create.return_value = AsyncMockStream()

        # Start listeners in the background
        llm_task = asyncio.create_task(handle_events())
        audio_task = asyncio.create_task(process_audio_chunks())

        # Allow them to subscribe
        await asyncio.sleep(0.1)

        # Subscribe to audio to verify output
        pubsub = self.redis.pubsub()
        await pubsub.subscribe('AUDIO_CHUNK_READY')

        # Publish mock detection
        mock_img = base64.b64encode(b"mock_image_data").decode('utf-8')
        payload = {
            "metadata": {"id": 1, "attributes": ["mock test attributes"]},
            "image_b64": mock_img
        }
        await self.redis.publish('CUSTOMER_DETECTED', json.dumps(payload))

        # Wait for processing
        await asyncio.sleep(0.5)

        # Check audio output messages
        received_chunks = []
        timeout = 2.0
        start_time = asyncio.get_event_loop().time()

        while len(received_chunks) < 3 and (asyncio.get_event_loop().time() - start_time) < timeout:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                received_chunks.append(message['data'].decode('utf-8'))
            else:
                await asyncio.sleep(0.05)

        # The stream is chunked by sentence
        self.assertIn("Hey there!", received_chunks)
        self.assertIn("Nice jacket.", received_chunks)
        self.assertIn("Come look at this.", received_chunks)

        llm_task.cancel()
        audio_task.cancel()
        try:
            await llm_task
            await audio_task
        except asyncio.CancelledError:
            pass

        await self.redis.aclose()

if __name__ == '__main__':
    unittest.main()