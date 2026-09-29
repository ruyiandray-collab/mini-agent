"""
记忆系统（两层）：
  - 短期记忆：对话历史 history.json。程序重启后接着聊；太长时只保留最近几轮，防止超出模型上下文长度。
  - 长期记忆：重要事实 facts.json。由 Agent 调用 remember 工具主动写入，每次对话都注入到系统提示词里。
"""
import json
from pathlib import Path

MEMORY_DIR = Path(__file__).parent / "memory"
HISTORY_FILE = MEMORY_DIR / "history.json"
FACTS_FILE = MEMORY_DIR / "facts.json"
MAX_TURNS = 20  # 短期记忆最多保留最近 20 轮对话（一轮 = 用户提问 + Agent 完成回答）


def _load(path: Path) -> list:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []  # 文件损坏时当作没有记忆，而不是让程序崩溃


def _save(path: Path, data: list):
    MEMORY_DIR.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- 短期记忆 ----------

def load_history() -> list:
    return _load(HISTORY_FILE)


def save_history(messages: list):
    """保存对话历史（不含系统提示词），只保留最近 MAX_TURNS 轮。
    必须按「轮」裁剪，从某条 user 消息开始切：如果从中间切，可能留下没有配对 tool 结果的
    tool_calls 消息，就会触发之前遇到的 400 错误。"""
    user_indexes = [i for i, m in enumerate(messages) if m["role"] == "user"]
    if len(user_indexes) > MAX_TURNS:
        messages = messages[user_indexes[-MAX_TURNS]:]
    _save(HISTORY_FILE, messages)


def clear_history():
    HISTORY_FILE.unlink(missing_ok=True)


# ---------- 长期记忆 ----------

def load_facts() -> list:
    return _load(FACTS_FILE)


def add_fact(fact: str) -> str:
    facts = load_facts()
    if fact in facts:
        return "这条信息已经记住过了"
    facts.append(fact)
    _save(FACTS_FILE, facts)
    return f"已记住：{fact}"


def forget_fact(keyword: str) -> str:
    facts = load_facts()
    kept = [f for f in facts if keyword not in f]
    removed = len(facts) - len(kept)
    _save(FACTS_FILE, kept)
    return f"已删除 {removed} 条包含「{keyword}」的记忆" if removed else f"没有找到包含「{keyword}」的记忆"
