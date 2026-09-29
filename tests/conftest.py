"""pytest 会自动加载本文件：让所有测试把记忆写到临时目录，不碰你真实的 memory/ 文件夹。"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import memory  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_memory(monkeypatch, tmp_path):
    monkeypatch.setattr(memory, "MEMORY_DIR", tmp_path)
    monkeypatch.setattr(memory, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr(memory, "FACTS_FILE", tmp_path / "facts.json")
