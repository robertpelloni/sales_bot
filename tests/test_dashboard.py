import os
import unittest
from fastapi.testclient import TestClient
from src.dashboard import app

class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_read_dashboard(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Project Sirens Central Hub", response.text)

    def test_get_inventory(self):
        response = self.client.get("/api/inventory")
        self.assertEqual(response.status_code, 200)
        self.assertIn("store_name", response.json())

if __name__ == '__main__':
    unittest.main()
