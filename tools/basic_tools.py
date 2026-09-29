"""基础工具：获取当前时间、计算器。"""
import ast
import operator
from datetime import datetime


def get_current_time() -> str:
    """返回当前本地时间。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 计算器只允许这些运算，避免直接用 eval() 执行任意代码（安全考虑）
_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("只支持数字和 + - * / ** % 运算")


def calculator(expression: str) -> str:
    """安全地计算数学表达式，例如 '(3 + 5) * 2'。"""
    tree = ast.parse(expression, mode="eval")
    return str(_eval_node(tree.body))
