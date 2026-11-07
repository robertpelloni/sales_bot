"""Outbound CRM Webhook Dispatch Engine for Project Sirens.

Dispatches interaction logs and qualified lead events to external CRMs
(HubSpot, Salesforce, Zapier, Webhook Relay) asynchronously with HMAC-SHA256 signature
verification.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "webhooks.json")


class WebhookManager:
    """Manages webhook configurations and non-blocking asynchronous dispatching."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.abspath(DEFAULT_CONFIG_PATH)
        self.config: Dict[str, Any] = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Loads webhook configuration from JSON file or initializes defaults."""
        defaults = {
            "enabled": False,
            "url": "",
            "secret": "",
            "events": ["NEW_INTERACTION", "LEAD_QUALIFIED"],
            "timeout_seconds": 5.0,
            "max_retries": 1
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    defaults.update(data)
            except Exception as e:
                logger.error(f"Error loading webhook config from {self.config_path}: {e}")
        return defaults

    def save_config(self, new_config: Dict[str, Any]) -> None:
        """Persists updated webhook configuration to disk."""
        self.config.update(new_config)
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save webhook config to {self.config_path}: {e}")

    def sign_payload(self, payload_bytes: bytes, secret: str) -> str:
        """Generates HMAC-SHA256 signature string for outbound payload verification."""
        if not secret:
            return ""
        return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    async def dispatch_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Schedules asynchronous dispatch of an event payload if webhooks are enabled."""
        if not self.config.get("enabled", False) or not self.config.get("url"):
            return False

        configured_events = self.config.get("events", [])
        if event_type not in configured_events:
            return False

        payload = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }

        # Spawn non-blocking background dispatch task to prevent blocking the event loop
        asyncio.create_task(self._send_http_request(payload))
        return True

    async def _send_http_request(self, payload: Dict[str, Any]) -> bool:
        """Executes HTTP POST request in an executor thread with timeout and HMAC signature."""
        url = self.config.get("url", "")
        secret = self.config.get("secret", "")
        timeout = float(self.config.get("timeout_seconds", 5.0))

        if not url:
            return False

        raw_payload = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "ProjectSirens-Webhook/1.5.0"
        }
        if secret:
            headers["X-Sirens-Signature"] = self.sign_payload(raw_payload, secret)

        def _blocking_post() -> bool:
            try:
                req = urllib.request.Request(url, data=raw_payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return 200 <= resp.status < 300
            except urllib.error.HTTPError as he:
                logger.warning(f"Webhook HTTP error {he.code} when dispatching to {url}: {he.reason}")
                return False
            except Exception as ex:
                logger.warning(f"Webhook connection failure dispatching to {url}: {ex}")
                return False

        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(None, _blocking_post)
        except Exception as e:
            logger.error(f"Failed to execute webhook dispatch executor: {e}")
            return False


webhook_manager = WebhookManager()
