import pytest
import numpy as np
from unittest.mock import MagicMock
from src.vision import (
    load_vision_model,
    MockYOLO,
    calculate_proximity,
    extract_visual_attributes,
    is_target_dwelling
)


def test_load_vision_model_fallback(tmp_path):
    """When model files are missing, load_vision_model falls back gracefully to MockYOLO."""
    non_existent_coral = str(tmp_path / "non_existent_coral.tflite")
    non_existent_pt = str(tmp_path / "non_existent.pt")

    model, model_type = load_vision_model(
        model_path=non_existent_coral,
        pytorch_fallback=non_existent_pt
    )

    assert isinstance(model, MockYOLO)
    assert model_type == "mock"

    res = model.track(None)
    assert len(res) == 1
    assert hasattr(res[0], 'boxes')
    assert res[0].boxes.id == [1]


def test_load_vision_model_coral_preference(monkeypatch, tmp_path):
    """When a Coral Edge TPU model file exists, it is loaded preferentially."""
    fake_coral_path = tmp_path / "yolo11n_edgetpu.tflite"
    fake_coral_path.write_text("fake tflite binary data")

    fake_pt_path = tmp_path / "yolo11n.pt"
    fake_pt_path.write_text("fake pt binary data")

    mock_yolo_constructor = MagicMock()
    monkeypatch.setattr("src.vision.YOLO", mock_yolo_constructor)

    model, model_type = load_vision_model(
        model_path=str(fake_coral_path),
        pytorch_fallback=str(fake_pt_path)
    )

    assert model_type == "coral_edgetpu"
    mock_yolo_constructor.assert_called_once_with(str(fake_coral_path))


def test_proximity_calculation():
    """Verifies that calculate_proximity maps bounding box heights to distances correctly."""
    # Close customer: height fills > 65% of 480p frame (350px)
    dist_close, desc_close = calculate_proximity([100, 50, 250, 400], frame_height=480)
    assert dist_close <= 1.2
    assert "close" in desc_close

    # Mid-range customer: height fills ~40% of 480p frame (200px)
    dist_mid, desc_mid = calculate_proximity([100, 100, 250, 300], frame_height=480)
    assert 1.2 < dist_mid < 2.5
    assert "mid-range" in desc_mid

    # Far customer: small bounding box (<20% of frame)
    dist_far, desc_far = calculate_proximity([100, 100, 150, 180], frame_height=480)
    assert dist_far >= 2.5
    assert "far" in desc_far


def test_dwell_time_trigger():
    """Verifies that is_target_dwelling triggers only when the duration meets or exceeds 1.5 seconds."""
    first_seen = 100.0

    # 1.0 second elapsed (under threshold)
    assert is_target_dwelling(first_seen, 101.0, threshold_seconds=1.5) is False

    # 1.49 seconds elapsed (just under threshold)
    assert is_target_dwelling(first_seen, 101.49, threshold_seconds=1.5) is False

    # 1.5 seconds elapsed (at threshold)
    assert is_target_dwelling(first_seen, 101.5, threshold_seconds=1.5) is True

    # 3.0 seconds elapsed (well over threshold)
    assert is_target_dwelling(first_seen, 103.0, threshold_seconds=1.5) is True


def test_color_extraction():
    """Verifies that extract_visual_attributes correctly identifies apparel color traits."""
    # Create blue dummy crop (BGR: 200, 50, 20)
    blue_crop = np.zeros((100, 80, 3), dtype=np.uint8)
    blue_crop[:, :] = [180, 50, 20]
    attrs_blue = extract_visual_attributes(blue_crop)
    assert any("blue" in a.lower() for a in attrs_blue)

    # Create dark dummy crop (BGR: 15, 15, 15)
    dark_crop = np.zeros((100, 80, 3), dtype=np.uint8)
    dark_crop[:, :] = [15, 15, 15]
    attrs_dark = extract_visual_attributes(dark_crop)
    assert any("dark" in a.lower() for a in attrs_dark)

    # Empty crop fallback
    assert extract_visual_attributes(None) == ["casual attire", "customer"]
