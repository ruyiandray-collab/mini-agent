"""记忆系统测试。"""
import memory
from agent import build_system_prompt


def test_facts_add_forget_and_prompt_injection():
    memory.add_fact("用户叫小明")
    assert memory.add_fact("用户叫小明") == "这条信息已经记住过了"   # 不重复记
    assert "用户叫小明" in build_system_prompt()                     # 注入系统提示词
    memory.forget_fact("小明")
    assert memory.load_facts() == []


def test_history_trim_keeps_whole_turns(monkeypatch):
    monkeypatch.setattr(memory, "MAX_TURNS", 1)
    history = [
        {"role": "user", "content": "第一轮"},
        {"role": "assistant", "tool_calls": [{"id": "c1"}]},
        {"role": "tool", "tool_call_id": "c1", "content": "结果"},
        {"role": "assistant", "content": "答1"},
        {"role": "user", "content": "第二轮"},
        {"role": "assistant", "content": "答2"},
    ]
    memory.save_history(history)
    # 只剩最后一轮，并且从 user 消息开始，不会留下没配对的 tool_calls
    assert memory.load_history() == history[4:]


def test_corrupted_file_does_not_crash():
    memory.MEMORY_DIR.mkdir(exist_ok=True)
    memory.HISTORY_FILE.write_text("{这不是合法的 JSON", encoding="utf-8")
    assert memory.load_history() == []
