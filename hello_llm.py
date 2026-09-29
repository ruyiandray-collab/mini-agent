"""
第 2 天练习：第一次调用大模型。
运行：python hello_llm.py
能看到 DeepSeek 的回答，说明 API Key 和网络都没问题。
"""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # 从 .env 文件读取配置到环境变量

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("BASE_URL", "https://api.deepseek.com"),
)

# messages 是一个列表，每条消息都有 role（谁说的）和 content（说了什么）
messages = [
    {"role": "system", "content": "你是一个友好的助手，回答尽量简短。"},
    {"role": "user", "content": "用一句话介绍一下你自己。"},
]

response = client.chat.completions.create(
    model=os.getenv("MODEL", "deepseek-chat"),
    messages=messages,
)

print(response.choices[0].message.content)
