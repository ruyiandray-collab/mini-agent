"""工具测试：运行 python -m pytest（不需要 API Key）。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import execute_tool  # noqa: E402


def call(name, **kwargs):
    return execute_tool(name, json.dumps(kwargs))


def test_calculator():
    assert call("calculator", expression="(3 + 5) * 2") == "16"


def test_calculator_rejects_code():
    assert call("calculator", expression="__import__('os')").startswith("错误")


def test_write_then_read():
    call("write_file", path="_test/hello.txt", content="你好")
    assert call("read_file", path="_test/hello.txt") == "你好"
    assert "hello.txt" in call("list_dir", path="_test")


def test_sandbox_blocks_escape():
    assert "PermissionError" in call("read_file", path="../agent.py")


def test_unknown_tool():
    assert call("no_such_tool").startswith("错误")
