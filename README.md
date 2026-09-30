# MiniAgent：从零实现的工具调用型 AI Agent

一个运行在命令行里的 AI Agent：接收自然语言任务后，**自主决定调用哪些工具、调用几次**，多步完成文件处理、计算、信息记忆等任务。

项目**不依赖 LangChain 等 Agent 框架**，Agent Loop、工具系统、记忆系统均为手写，重点在于把 Agent 的每个环节做得可解释、可测试、可评测。

| 指标 | 结果 |
|---|---|
| 自建评测集成功率 | **45/45（100%）**：15 个任务 × 3 次，覆盖单工具 / 多步 / 记忆 / 鲁棒性 |
| 平均执行步数 / 耗时 | 2.1 步 / 1.5 秒 |
| 单元测试 | 10 个，使用假模型，不消耗 API |
| 代码量 | 核心约 330 行 + 评测约 160 行 Python（含注释） |

> 详细评测结果见 [eval/results/report.md](eval/results/report.md)，模型为 DeepSeek `deepseek-chat`。

---

## 演示

```
你：看看 notes 文件夹里有什么，把所有 txt 的内容汇总成 notes/summary.md
🔧 第 1 步 调用 list_dir({"path": "notes"})
🔧 第 2 步 调用 read_file({"path": "notes/monday.txt"})
🔧 第 2 步 调用 read_file({"path": "notes/tuesday.txt"})
🔧 第 2 步 调用 read_file({"path": "notes/wednesday.txt"})
🔧 第 3 步 调用 write_file({"path": "notes/summary.md", "content": "# Notes 汇总 ..."})
MiniAgent：已完成。notes 里有 3 个 txt 文件，已按周一到周三汇总写入 notes/summary.md。

你：我是 Ray，我喜欢玩游戏
🔧 第 1 步 调用 remember({"fact": "用户叫 Ray，喜欢玩游戏"})
MiniAgent：记住啦！

（退出程序、重新启动、输入 /clear 清空对话历史之后）
你：我是谁？
MiniAgent：你叫 Ray，喜欢玩游戏。
```

---

## 架构

```
             ┌──────────────── Agent Loop（agent.py）────────────────┐
用户输入 ──► │ messages ──► DeepSeek API ──► 有 tool_calls？           │
             │    ▲                            │是          │否       │ ──► 最终回答
             │    │                            ▼            └────────┼──►
             │    └──── 工具结果（按 tool_call_id 配对）◄── 工具注册表 │
             └──────────────────────────────────────────────────────────┘
                     ▲ 系统提示词注入                      │
               ┌─────┴──────────────┐          ┌──────────┴──────────────┐
               │ 记忆系统 memory.py  │          │ 工具系统 tools/          │
               │ · 短期：对话历史     │          │ · 时间 / 计算器          │
               │ · 长期：用户事实     │◄─────────│ · 文件读写（沙箱）       │
               └────────────────────┘ remember │ · remember / forget     │
                                               └─────────────────────────┘
```

| 模块 | 文件 | 职责 |
|---|---|---|
| Agent Loop | `agent.py` | 循环调用模型、执行工具，最大步数保护，错误重试与历史回滚，运行统计 |
| 工具系统 | `tools/` | 工具注册表（函数 + JSON Schema），统一执行入口与错误处理 |
| 记忆系统 | `memory.py` | 短期记忆（对话持久化与按轮裁剪）+ 长期记忆（事实存储） |
| 评测 | `eval/` | 15 个任务的自动评测，统计成功率、步数、token、耗时 |
| 入口 | `main.py` | 命令行交互，`/clear` 清空对话历史 |

---

## 关键设计

**1. Agent Loop：由模型决定何时结束**
每一轮把完整对话发给模型：如果返回 `tool_calls` 就执行工具、把结果写回对话，再进入下一轮；如果没有返回 `tool_calls`，就视为任务完成。另外设有 `max_steps=10` 作为兜底，防止模型陷入死循环。

**2. 错误分级处理**
- **工具错误**（文件不存在、参数错误等）不会让程序崩溃，而是转成文字返回给模型，由模型自行调整做法。评测中，`missing_file` 任务的 Agent 会先读文件，失败后再列目录确认，然后如实告诉用户
- **API 错误**分成可重试和不可重试两类：网络断开、429、5xx 会按递增间隔重试；400 这类请求本身写错的错误直接报出，不做无效重试
- **失败回滚**：一轮对话中途出错时，删除本轮已写入的消息，保证对话历史格式始终合法

**3. 两层记忆**

| | 短期记忆 | 长期记忆 |
|---|---|---|
| 内容 | 最近 20 轮原始对话 | 提炼出的用户事实 |
| 写入方式 | 每轮成功后自动保存 | **由 Agent 自主判断**，调用 `remember` / `forget` |
| 使用方式 | 加载进 messages | 每次调用模型前注入系统提示词 |

对话历史裁剪时**必须从 user 消息处切分**：如果从中间切，可能留下没有对应工具结果的 `tool_calls`，导致 API 返回 400。这个问题是开发中通过实验发现的，详见 [docs/DESIGN.md](docs/DESIGN.md)。

**4. 安全边界**
- 文件工具只能访问 `workspace/` 目录，路径穿越（如 `../.env`）会被拦截
- 计算器用 AST 白名单实现，不使用 `eval()`，避免执行任意代码
- API Key、记忆和日志都不纳入版本控制

---

## 快速开始

```bash
git clone https://github.com/ruyiandray-collab/mini-agent.git
cd mini-agent
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # 填入 DeepSeek API Key（macOS/Linux 用 cp）
python main.py
```

```bash
python -m pytest -q               # 单元测试（无需 API Key）
python -m eval.run_eval --repeat 3   # 自动评测（需要 API Key，费用约几分钱）
```

更换模型：只需修改 `.env` 中的 `BASE_URL` 和 `MODEL`，支持任何兼容 OpenAI 接口的模型。

---

## 局限与后续计划

- 评测集规模较小（15 个任务），且由作者自行设计，任务难度偏低；后续计划加入更难的长链路任务，并对比不同模型的表现
- 长期记忆目前全部注入系统提示词，记忆条目很多时会占用上下文 → 计划改为向量检索，只注入相关条目
- 对话历史只做裁剪、不做压缩 → 计划对旧对话自动生成摘要
- 工具扩展：网页搜索、沙箱内执行 Python、接入 MCP 协议
