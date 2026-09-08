"""
Deterministic Mathematical Calculation Tool (SIH26117).
Evaluates arithmetic expressions deterministically using AST inspection.
Zero untrusted eval() execution to guarantee sovereign runtime security.
"""

import ast
import operator
import math
from typing import Dict, Any, Union

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos
}

_SAFE_FUNCS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "ceil": math.ceil,
    "floor": math.floor
}


def _eval_node(node: ast.AST) -> Union[int, float]:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in _SAFE_OPS:
            return _SAFE_OPS[op_type](_eval_node(node.operand))
        raise ValueError(f"Unsupported unary operator: {op_type}")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in _SAFE_OPS:
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            return _SAFE_OPS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type}")

    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in _SAFE_FUNCS:
            args = [_eval_node(arg) for arg in node.args]
            return _SAFE_FUNCS[node.func.id](*args)
        raise ValueError(f"Function '{getattr(node.func, 'id', 'unknown')}' is not authorized.")

    raise ValueError(f"Unsupported AST node: {type(node)}")


def calculation_tool(expression: str) -> Dict[str, Any]:
    """
    Evaluates safe deterministic mathematical expressions.
    Supports basic arithmetic (+, -, *, /, %, **) and math functions (abs, round, min, max, sqrt).
    """
    clean_expr = expression.strip()
    try:
        parsed = ast.parse(clean_expr, mode="eval")
        result = _eval_node(parsed.body)
        return {
            "expression": clean_expr,
            "result": result,
            "status": "SUCCESS"
        }
    except Exception as e:
        return {
            "expression": clean_expr,
            "result": None,
            "error": f"Calculation error: {str(e)}",
            "status": "FAILED"
        }
