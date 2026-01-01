"""
pytest 配置和共享 fixtures
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from hypothesis import settings, Verbosity

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Hypothesis 配置
settings.register_profile("default", max_examples=100, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=200, verbosity=Verbosity.verbose)
settings.register_profile("debug", max_examples=10, verbosity=Verbosity.verbose)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "default"))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录用于测试"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db_path(temp_dir: Path) -> Path:
    """创建临时数据库路径"""
    return temp_dir / "test.db"


@pytest.fixture
def sample_config() -> dict:
    """示例配置数据"""
    return {
        "theme": "dark_green",
        "language": "zh_CN",
        "reading": {
            "page_direction": "vertical",
            "dual_page": False,
            "continuous_scroll": True,
            "toolbar_position": "top",
            "eye_protection": False,
            "keep_screen_on": True,
        },
        "stylus": {
            "double_tap": "eraser",
            "long_press": "select_text",
            "primary_click": "none",
            "secondary_click": "undo",
            "pinch": "none",
            "swipe_up": "none",
            "swipe_down": "none",
            "palm_rejection_sensitivity": 7,
        },
        "tools": {
            "shape_recognition": True,
            "pressure_sensitivity": True,
            "shape_fill": False,
            "long_press_select_text": True,
            "long_press_create_menu": True,
        },
        "backup": {
            "provider": "local",
            "auto_backup": False,
            "wifi_only": True,
        },
        "translation": {
            "default_direction": "en_to_zh",
            "api_provider": "baidu",
        },
    }
