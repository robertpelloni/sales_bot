import pytest
import os
import sys
from unittest.mock import MagicMock, patch

from src.tray_app import ServerManager, create_tray_icon_image, run_tray_controller, PIL_AVAILABLE


def test_server_manager_initial_state():
    sm = ServerManager()
    assert not sm.is_hub_running()
    assert not sm.is_kiosk_running()
    assert sm.hub_proc is None
    assert sm.kiosk_proc is None


def test_server_manager_lifecycle():
    sm = ServerManager()
    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc

        # Start Hub
        assert sm.start_hub() is True
        assert sm.is_hub_running() is True
        mock_popen.assert_called_once()

        # Start again should be idempotent
        assert sm.start_hub() is True

        # Stop Hub
        assert sm.stop_hub() is True
        mock_proc.terminate.assert_called_once()
        assert not sm.is_hub_running()

        # Start Kiosk
        assert sm.start_kiosk() is True
        assert sm.is_kiosk_running() is True

        # Stop Kiosk
        assert sm.stop_kiosk() is True
        assert not sm.is_kiosk_running()


def test_create_tray_icon_image():
    if not PIL_AVAILABLE:
        pytest.skip("Pillow not available")
    img = create_tray_icon_image(size=32)
    assert img is not None
    assert img.size == (32, 32)
    assert img.mode == "RGBA"


def test_run_tray_controller_headless():
    res = run_tray_controller(headless=True)
    assert isinstance(res, ServerManager)
    assert not res.is_hub_running()
