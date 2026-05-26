import pytest
from pathlib import Path
from PIL import Image
from converter.heif_converter import convert_image


@pytest.fixture
def small_jpeg(tmp_path):
    img = Image.new("RGB", (100, 60), color=(255, 0, 0))
    src = tmp_path / "src.jpg"
    img.save(str(src), "JPEG")
    return str(src)


def test_no_rotation_preserves_dimensions(small_jpeg, tmp_path):
    out = tmp_path / "out0"
    out.mkdir()
    dst = convert_image(small_jpeg, str(out), "JPEG", rotation=0)
    assert Image.open(dst).size == (100, 60)


def test_rotate_90_swaps_dimensions(small_jpeg, tmp_path):
    out = tmp_path / "out90"
    out.mkdir()
    dst = convert_image(small_jpeg, str(out), "JPEG", rotation=90)
    assert Image.open(dst).size == (60, 100)


def test_rotate_180_preserves_dimensions(small_jpeg, tmp_path):
    out = tmp_path / "out180"
    out.mkdir()
    dst = convert_image(small_jpeg, str(out), "JPEG", rotation=180)
    assert Image.open(dst).size == (100, 60)


def test_rotate_270_swaps_dimensions(small_jpeg, tmp_path):
    out = tmp_path / "out270"
    out.mkdir()
    dst = convert_image(small_jpeg, str(out), "JPEG", rotation=270)
    assert Image.open(dst).size == (60, 100)
