"""用一个「假模型」测试 Agent Loop 的流程，不消耗真实 API 额度。"""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent))

from openai.types.chat import ChatCompletionMessage  # noqa: E402

import agent as agent_module  # noqa: E402


def make_reply(message):
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeClient:
    """第一次回复：要求调用 calculator；第二次回复：给出最终答案。"""

    def __init__(self):
        self.replies = [
            ChatCompletionMessage.model_validate({
                "role": "assistant",
                "tool_calls": [{
                    "id": "call_1", "type": "function",
                    "function": {"name": "calculator", "arguments": '{"expression": "6 * 7"}'},
                }],
            }),
            ChatCompletionMessage(role="assistant", content="答案是 42"),
        ]
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        return make_reply(self.replies.pop(0))


def test_loop_calls_tool_then_answers(monkeypatch, tmp_path):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setattr(agent_module, "LOG_DIR", tmp_path)
    a = agent_module.Agent()
    a.client = FakeClient()

    assert a.run("6 乘以 7 是多少") == "答案是 42"
    tool_msgs = [m for m in a.messages if m["role"] == "tool"]
    assert tool_msgs[0]["content"] == "42"          # 工具结果被正确喂回模型
    assert list(tmp_path.glob("*.json"))           # 轨迹日志已保存


def test_error_not_retried_and_history_rolled_back(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    a = agent_module.Agent()
    calls = []

    def broken_create(**kwargs):
        calls.append(1)
        raise ValueError("模拟一个请求格式错误")

    a.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=broken_create)))
    before = list(a.messages)

    try:
        a.run("你好")
    except ValueError:
        pass
    assert len(calls) == 1          # 非临时故障：只调用一次，不重试
    assert a.messages == before     # 出错后历史被撤销，不留下残缺消息
