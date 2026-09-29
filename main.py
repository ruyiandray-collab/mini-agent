"""命令行入口：python main.py"""
from rich.console import Console
from rich.markdown import Markdown

from agent import Agent

console = Console()


def main():
    agent = Agent()
    turns = sum(1 for m in agent.messages if m["role"] == "user")
    console.print("[bold magenta]MiniAgent 已启动[/]（输入 exit 退出，/clear 清空对话历史）")
    if turns:
        console.print(f"[dim]已加载 {turns} 轮历史对话[/]")
    while True:
        try:
            user_input = console.input("\n[bold]你：[/]").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        if user_input == "/clear":
            agent.clear_history()
            console.print("[green]已清空对话历史（长期记忆仍保留）[/]")
            continue
        try:
            answer = agent.run(user_input)
        except Exception as e:
            # 出错时只提示，不让整个程序崩溃退出，可以继续提问
            console.print(f"[bold red]出错了：{type(e).__name__}: {e}[/]")
            continue
        console.print("[bold magenta]MiniAgent：[/]")
        console.print(Markdown(answer))
    console.print("再见！")


if __name__ == "__main__":
    main()
