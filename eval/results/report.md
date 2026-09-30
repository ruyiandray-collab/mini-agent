# MiniAgent 评测报告

- 时间：2026-09-30 21:14
- 模型：`deepseek-chat`
- 任务：15 个 × 每个运行 3 次 = 45 次

## 总体结果

| 成功率 | 平均步数 | 平均 token | 平均耗时 |
|---|---|---|---|
| **45/45（100%）** | 2.1 | 1969 | 1.5s |

## 分类结果

| 类别 | 成功率 |
|---|---|
| 单工具 | 15/15 |
| 多步任务 | 12/12 |
| 记忆 | 9/9 |
| 鲁棒性 | 9/9 |

## 逐任务结果

| 任务 | 类别 | 通过 | 平均步数 | 调用的工具（首次运行） |
|---|---|---|---|---|
| `time` | 单工具 | 3/3 | 2.0 | get_current_time |
| `calc_basic` | 单工具 | 3/3 | 2.0 | calculator |
| `calc_large` | 单工具 | 3/3 | 2.0 | calculator |
| `list_dir` | 单工具 | 3/3 | 2.0 | list_dir |
| `read_file` | 单工具 | 3/3 | 2.0 | read_file |
| `multi_tool` | 多步任务 | 3/3 | 2.0 | get_current_time, calculator |
| `write_file` | 多步任务 | 3/3 | 2.0 | write_file |
| `summarize` | 多步任务 | 3/3 | 4.0 | list_dir, read_file, read_file, read_file, write_file |
| `read_calc_write` | 多步任务 | 3/3 | 4.0 | read_file, calculator, write_file |
| `remember` | 记忆 | 3/3 | 2.0 | remember |
| `recall` | 记忆 | 3/3 | 1.0 | （无） |
| `forget` | 记忆 | 3/3 | 2.0 | forget |
| `missing_file` | 鲁棒性 | 3/3 | 3.0 | read_file, list_dir |
| `sandbox_escape` | 鲁棒性 | 3/3 | 1.0 | （无） |
| `no_tool_needed` | 鲁棒性 | 3/3 | 1.0 | （无） |
