"""文件工具：所有操作都被限制在 workspace/ 目录内（沙箱），防止 Agent 乱改电脑上的文件。"""
from pathlib import Path

WORKSPACE = (Path(__file__).parent.parent / "workspace").resolve()
WORKSPACE.mkdir(exist_ok=True)


def _safe_path(relative_path: str) -> Path:
    """把相对路径转换成 workspace 内的绝对路径；如果试图跳出 workspace 就报错。"""
    full = (WORKSPACE / relative_path).resolve()
    if not full.is_relative_to(WORKSPACE):
        raise PermissionError(f"禁止访问 workspace 之外的路径：{relative_path}")
    return full


def list_dir(path: str = ".") -> str:
    """列出目录下的文件和文件夹。"""
    target = _safe_path(path)
    if not target.is_dir():
        raise FileNotFoundError(f"目录不存在：{path}")
    items = [f"{p.name}/" if p.is_dir() else p.name for p in sorted(target.iterdir())]
    return "\n".join(items) if items else "（空目录）"


def read_file(path: str) -> str:
    """读取文本文件内容。"""
    target = _safe_path(path)
    if not target.is_file():
        raise FileNotFoundError(f"文件不存在：{path}")
    return target.read_text(encoding="utf-8-sig")  # -sig 兼容 Windows 记事本保存的带 BOM 文件


def write_file(path: str, content: str) -> str:
    """写入文本文件（会覆盖已有内容），自动创建所需的文件夹。"""
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"已写入 {path}（{len(content)} 个字符）"
