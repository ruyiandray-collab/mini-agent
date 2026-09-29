"""
⭐ Agent Loop 核心 ⭐

循环流程：
  1. 把对话历史 + 工具说明书发给模型
  2. 如果模型要求调用工具 → 执行工具，把结果追加到历史，回到第 1 步
  3. 如果模型直接给出文字回答 → 任务完成，返回答案
  4. 超过 max_steps 还没结束 → 强制停止，防止死循环
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import APIConnectionError, InternalServerError, OpenAI, RateLimitError
from rich.console import Console
from rich.panel import Panel

import memory
from tools import TOOL_SCHEMAS, execute_tool

load_dotenv()
console = Console()
LOG_DIR = Path(__file__).parent / "logs"

# 只有这些「临时故障」才值得重试：网络断开/超时、请求太频繁(429)、服务器内部错误(5xx)。
# 像 400 这种「请求本身写错了」的错误，重试多少次结果都一样，应该立刻报错。
RETRYABLE_ERRORS = (APIConnectionError, RateLimitError, InternalServerError)

SYSTEM_PROMPT = """你是 MiniAgent，一个能使用工具完成任务的助手。
- 需要信息或操作时，调用合适的工具；不要编造文件内容或计算结果。
- 可以连续调用多个工具，逐步完成任务。
- 所有文件操作都在工作区内进行，路径使用相对路径。
- 始终使用中文，包括调用工具前说明思路的话。
- 用户透露关于自己的重要长期信息（名字、偏好、目标等）时，用 remember 工具记下来。
- 任务完成后，用简洁的中文告诉用户你做了什么、结果是什么。"""


def build_system_prompt() -> str:
    """系统提示词 = 固定规则 + 长期记忆。每次调用模型前重新生成，这样刚记住的内容立刻生效。"""
    facts = memory.load_facts()
    if not facts:
        return SYSTEM_PROMPT
    return SYSTEM_PROMPT + "\n\n## 你记得的关于用户的信息\n" + "\n".join(f"- {f}" for f in facts)


class Agent:
    def __init__(self, max_steps: int = 10):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key or "在这里填" in api_key:
            raise RuntimeError("请先把 .env.example 复制为 .env，并填入你的 DeepSeek API Key")
        self.client = OpenAI(api_key=api_key, base_url=os.getenv("BASE_URL", "https://api.deepseek.com"))
        self.model = os.getenv("MODEL", "deepseek-chat")
        self.max_steps = max_steps
        # messages[0] 永远是系统提示词，后面接上次保存的对话历史（短期记忆）
        self.messages = [{"role": "system", "content": build_system_prompt()}] + memory.load_history()

    def clear_history(self):
        """清空短期记忆（长期记忆保留）。"""
        self.messages = self.messages[:1]
        memory.clear_history()

    def _call_llm(self, retries: int = 3):
        """调用模型；遇到临时故障时等待后重试，其他错误直接抛出。"""
        self.messages[0]["content"] = build_system_prompt()
        for attempt in range(1, retries + 1):
            try:
                return self.client.chat.completions.create(
                    model=self.model, messages=self.messages, tools=TOOL_SCHEMAS
                )
            except RETRYABLE_ERRORS as e:
                if attempt == retries:
                    raise
                console.print(f"[yellow]调用失败（{e}），{attempt * 2} 秒后第 {attempt + 1} 次尝试...[/]")
                time.sleep(attempt * 2)

    def run(self, user_input: str) -> str:
        # 记下本轮开始前的历史长度：如果中途出错，就把本轮写了一半的消息撤销，
        # 否则残缺的历史（比如缺了 tool 消息）会让之后的每次提问都报错
        history_len = len(self.messages)
        try:
            answer = self._run(user_input)
        except Exception:
            del self.messages[history_len:]
            raise
        memory.save_history(self.messages[1:])  # 成功完成一轮才保存，不含系统提示词
        return answer

    def _run(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})

        for step in range(1, self.max_steps + 1):
            msg = self._call_llm().choices[0].message
            # 转成普通字典再存入历史，方便之后保存成 JSON 日志
            self.messages.append(msg.model_dump(exclude_none=True))

            # 没有工具调用，说明模型认为任务已完成
            if not msg.tool_calls:
                self._save_log()
                return msg.content or ""

            # 模型在调用工具前说的话，相当于它的「思考过程」
            if msg.content:
                console.print(f"[dim]💭 {msg.content}[/]")

            for call in msg.tool_calls:
                name, args = call.function.name, call.function.arguments
                console.print(f"[cyan]🔧 第 {step} 步 调用 {name}({args})[/]")
                result = execute_tool(name, args)
                preview = result if len(result) < 300 else result[:300] + "..."
                console.print(Panel(preview, title="结果", border_style="green" if not result.startswith("错误") else "red"))
                self.messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

        self._save_log()
        return f"已达到最大步数 {self.max_steps}，任务未完成。"

    def _save_log(self):
        """把完整对话轨迹保存为 JSON，方便调试和复盘。"""
        LOG_DIR.mkdir(exist_ok=True)
        path = LOG_DIR / f"{datetime.now():%Y%m%d_%H%M%S}.json"
        path.write_text(json.dumps(self.messages, ensure_ascii=False, indent=2), encoding="utf-8")
