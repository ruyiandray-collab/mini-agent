"""
工具注册表：把「工具名」映射到「Python 函数 + 给模型看的说明书（JSON Schema）」。
新增一个工具只需要两步：写好函数，在 TOOLS 里加一条。
"""
import json

from .basic_tools import calculator, get_current_time
from .file_tools import list_dir, read_file, write_file
from memory import add_fact, forget_fact


def _schema(name, description, properties=None, required=None):
    """生成 OpenAI 格式的工具说明书，减少重复代码。"""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties or {},
                "required": required or [],
            },
        },
    }


TOOLS = {
    "get_current_time": {
        "func": get_current_time,
        "schema": _schema("get_current_time", "获取当前的本地日期和时间"),
    },
    "calculator": {
        "func": calculator,
        "schema": _schema(
            "calculator",
            "计算数学表达式，支持 + - * / ** % 和括号",
            {"expression": {"type": "string", "description": "例如 '(3 + 5) * 2'"}},
            ["expression"],
        ),
    },
    "list_dir": {
        "func": list_dir,
        "schema": _schema(
            "list_dir",
            "列出工作区中某个目录的文件和子目录",
            {"path": {"type": "string", "description": "相对路径，默认 '.' 表示工作区根目录"}},
        ),
    },
    "read_file": {
        "func": read_file,
        "schema": _schema(
            "read_file",
            "读取工作区中一个文本文件的全部内容",
            {"path": {"type": "string", "description": "文件的相对路径"}},
            ["path"],
        ),
    },
    "write_file": {
        "func": write_file,
        "schema": _schema(
            "write_file",
            "把文本写入工作区中的文件（会覆盖原内容）",
            {
                "path": {"type": "string", "description": "文件的相对路径"},
                "content": {"type": "string", "description": "要写入的完整内容"},
            },
            ["path", "content"],
        ),
    },
    "remember": {
        "func": add_fact,
        "schema": _schema(
            "remember",
            "把关于用户的重要、长期有效的信息存入长期记忆（如名字、偏好、目标），以后的对话都能看到。"
            "不要记录临时性的内容。",
            {"fact": {"type": "string", "description": "一句简洁的陈述，例如 '用户叫小明，正在学习 Python'"}},
            ["fact"],
        ),
    },
    "forget": {
        "func": forget_fact,
        "schema": _schema(
            "forget",
            "当用户要求忘掉某件事，或某条记忆已经过时时，删除包含关键词的长期记忆",
            {"keyword": {"type": "string", "description": "要删除的记忆中包含的关键词"}},
            ["keyword"],
        ),
    },
}

# 发送给模型的工具说明书列表
TOOL_SCHEMAS = [t["schema"] for t in TOOLS.values()]


def execute_tool(name: str, arguments_json: str) -> str:
    """执行工具。任何错误都转成文字返回给模型，而不是让程序崩溃——模型看到错误后往往能自己纠正。"""
    if name not in TOOLS:
        return f"错误：不存在名为 {name} 的工具"
    try:
        args = json.loads(arguments_json or "{}")
        return str(TOOLS[name]["func"](**args))
    except Exception as e:
        return f"错误：{type(e).__name__}: {e}"
