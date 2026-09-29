# MiniAgent

从零实现的命令行 AI Agent，不依赖 LangChain 等框架。基于 DeepSeek（兼容 OpenAI 接口），能自主决定调用工具、多步完成任务。

## 功能亮点

- **手写 Agent Loop**：模型 → 工具调用 → 结果回填 → 循环直到完成，并有最大步数保护
- **可扩展的工具注册表**：新增工具只需写一个函数，再加一条 Schema
- **安全沙箱**：文件操作限制在 `workspace/` 内，计算器不使用 `eval`
- **可观测性**：终端实时显示每一步调用；完整轨迹保存到 `logs/*.json`
- **两层记忆系统**：短期记忆（对话历史持久化，按完整轮次裁剪，保证消息格式合法）+ 长期记忆（Agent 通过 `remember`/`forget` 工具自主管理，注入系统提示词）
- **容错**：工具出错时把错误信息返回给模型自我纠正；只对临时故障（网络、429、5xx）重试；出错时回滚本轮对话历史
- **测试覆盖**：用假模型测试循环逻辑，不消耗 API 额度

## 架构

```
用户输入 ─► Agent.run() ─► DeepSeek API ─┬─ 有 tool_calls ─► execute_tool() ─┐
                ▲                        │                                  │
                └──── 结果追加到 messages ◄─────────────────────────────────┘
                                         └─ 无 tool_calls ─► 返回最终回答
```

| 文件 | 作用 |
|---|---|
| `agent.py` | Agent Loop 核心 |
| `tools/__init__.py` | 工具注册表与统一执行入口 |
| `tools/basic_tools.py` | 时间、计算器 |
| `tools/file_tools.py` | 列目录、读文件、写文件（沙箱） |
| `memory.py` | 短期记忆（对话历史）与长期记忆（事实） |
| `main.py` | 命令行交互入口（`/clear` 清空对话历史） |

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # 然后在 .env 里填入 DeepSeek API Key
python main.py
```

试试这些问题：
- `现在几点？再帮我算一下 (1024 - 24) * 3`
- `看看 notes 文件夹里有什么，把所有 txt 的内容汇总成 notes/summary.md`

运行测试：`python -m pytest -q`

## 后续计划

- [x] 对话历史持久化 + 长期事实记忆
- [ ] 记忆升级：旧对话自动摘要 → 向量检索
- [ ] 更多工具：网页搜索、沙箱内执行 Python
- [ ] 规划模式：先制定计划，再逐步执行
