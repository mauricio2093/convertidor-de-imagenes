import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def dirs(tmp_path):
    """Carpetas de entrada y salida vacias."""
    src = tmp_path / "in"
    src.mkdir()
    return src, tmp_path / "out"


@pytest.fixture
def make_image():
    def _make(path, size=(64, 48), mode="RGB", color=(200, 30, 30), **save_args):
        Image.new(mode, size, color).save(path, **save_args)
        return path
    return _make
