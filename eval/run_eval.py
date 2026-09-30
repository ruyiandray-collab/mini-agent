"""
自动评测：用真实模型逐个运行 tasks.py 里的任务，统计成功率、步数、token、耗时。
运行：python -m eval.run_eval --repeat 3
每个任务都在独立的临时工作区和临时记忆里运行，互不干扰，也不会碰你真实的 workspace/ 和 memory/。
结果写入 eval/results/report.md 和 results.json。
"""
import argparse
import json
import tempfile
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import agent as agent_module
import memory
import tools.file_tools as file_tools
from agent import Agent
from eval.tasks import TASKS

RESULTS_DIR = Path(__file__).parent / "results"


def run_task(task: dict) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="mini_agent_eval_"))
    ws = tmp / "workspace"
    ws.mkdir()
    # 把工作区、记忆、日志都指向临时目录
    file_tools.WORKSPACE = ws.resolve()
    memory.MEMORY_DIR = tmp / "memory"
    memory.HISTORY_FILE = memory.MEMORY_DIR / "history.json"
    memory.FACTS_FILE = memory.MEMORY_DIR / "facts.json"
    agent_module.LOG_DIR = tmp / "logs"

    for rel, content in task.get("files", {}).items():
        (ws / rel).parent.mkdir(parents=True, exist_ok=True)
        (ws / rel).write_text(content, encoding="utf-8")
    for fact in task.get("facts", []):
        memory.add_fact(fact)

    agent = Agent(verbose=False)
    start = time.perf_counter()
    try:
        answer, error = agent.run(task["prompt"]), None
    except Exception as e:
        answer, error = "", f"{type(e).__name__}: {e}"
    latency = time.perf_counter() - start

    stats = agent.stats or {"steps": 0, "tool_calls": [], "prompt_tokens": 0, "completion_tokens": 0}
    try:
        passed = error is None and bool(task["check"](answer, stats, ws, memory.load_facts()))
    except Exception:
        passed = False
    return {
        "id": task["id"], "category": task["category"], "passed": passed,
        "steps": stats["steps"], "tool_calls": stats["tool_calls"],
        "tokens": stats["prompt_tokens"] + stats["completion_tokens"],
        "latency": round(latency, 2), "answer": answer, "error": error,
    }


def summarize(results: list, model: str, repeat: int) -> str:
    n = len(results)
    ok = sum(r["passed"] for r in results)
    avg = lambda key: sum(r[key] for r in results) / n  # noqa: E731

    lines = [
        "# MiniAgent 评测报告", "",
        f"- 时间：{datetime.now():%Y-%m-%d %H:%M}",
        f"- 模型：`{model}`",
        f"- 任务：{len(TASKS)} 个 × 每个运行 {repeat} 次 = {n} 次",
        "", "## 总体结果", "",
        "| 成功率 | 平均步数 | 平均 token | 平均耗时 |", "|---|---|---|---|",
        f"| **{ok}/{n}（{ok / n:.0%}）** | {avg('steps'):.1f} | {avg('tokens'):.0f} | {avg('latency'):.1f}s |",
        "", "## 分类结果", "", "| 类别 | 成功率 |", "|---|---|",
    ]
    by_cat = defaultdict(list)
    for r in results:
        by_cat[r["category"]].append(r["passed"])
    for cat, ps in by_cat.items():
        lines.append(f"| {cat} | {sum(ps)}/{len(ps)} |")

    lines += ["", "## 逐任务结果", "", "| 任务 | 类别 | 通过 | 平均步数 | 调用的工具（首次运行） |", "|---|---|---|---|---|"]
    by_task = defaultdict(list)
    for r in results:
        by_task[r["id"]].append(r)
    for tid, rs in by_task.items():
        passed = sum(r["passed"] for r in rs)
        steps = sum(r["steps"] for r in rs) / len(rs)
        tools_used = ", ".join(rs[0]["tool_calls"]) or "（无）"
        lines.append(f"| `{tid}` | {rs[0]['category']} | {passed}/{len(rs)} | {steps:.1f} | {tools_used} |")

    failed = [r for r in results if not r["passed"]]
    if failed:
        lines += ["", "## 失败案例", ""]
        for r in failed:
            detail = r["error"] or r["answer"].replace("\n", " ")[:150]
            lines.append(f"- `{r['id']}`：{detail}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeat", type=int, default=1, help="每个任务运行几次（模型输出有随机性）")
    args = parser.parse_args()

    results = []
    for task in TASKS:
        for i in range(args.repeat):
            r = run_task(task)
            results.append(r)
            print(f"{'✅' if r['passed'] else '❌'} {task['id']} #{i + 1}  步数={r['steps']}  {r['latency']}s")

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    report = summarize(results, Agent(verbose=False).model, args.repeat)
    (RESULTS_DIR / "report.md").write_text(report, encoding="utf-8")
    print("\n" + report)


if __name__ == "__main__":
    main()
