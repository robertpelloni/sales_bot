import pytest
from unittest.mock import MagicMock
from src.vision import load_vision_model, MockYOLO


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

    # Verify mock track outputs valid bounding box contract
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

    # Mock YOLO constructor to avoid loading invalid binary file
    mock_yolo_constructor = MagicMock()
    monkeypatch.setattr("src.vision.YOLO", mock_yolo_constructor)

    model, model_type = load_vision_model(
        model_path=str(fake_coral_path),
        pytorch_fallback=str(fake_pt_path)
    )

    assert model_type == "coral_edgetpu"
    mock_yolo_constructor.assert_called_once_with(str(fake_coral_path))
