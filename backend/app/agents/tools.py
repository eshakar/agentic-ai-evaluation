"""Tools exposed to the Claude agent. Add your own here and register them in TOOLS and HANDLERS."""

import ast
import operator
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

MAX_EXPONENT = 1000  # stops inputs like 9**9**9 from freezing the server
MAX_RESULT_BITS = 4096


def _bounded_pow(base: float, exp: float) -> float:
    if abs(exp) > MAX_EXPONENT:
        raise ValueError(f"Exponent too large (max {MAX_EXPONENT})")
    return operator.pow(base, exp)


_OPS: dict[type, Callable[..., Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: _bounded_pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        result = _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
        if isinstance(result, int) and result.bit_length() > MAX_RESULT_BITS:
            raise ValueError("Result too large")
        return result
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Unsupported expression")


def calculator(expression: str) -> str:
    result = _safe_eval(ast.parse(expression, mode="eval"))
    if isinstance(result, float) and result.is_integer():
        return str(int(result))
    return str(result)


def current_utc_time() -> str:
    return datetime.now(UTC).isoformat()


TOOLS: list[dict[str, Any]] = [
    {
        "name": "calculator",
        "description": "Evaluate an arithmetic expression (+, -, *, /, **, %). Use for math.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "e.g. '(12 + 3) * 4'"}},
            "required": ["expression"],
            "additionalProperties": False,
        },
    },
    {
        "name": "current_utc_time",
        "description": "Return the current date and time in UTC (ISO 8601).",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
]

HANDLERS: dict[str, Callable[..., str]] = {
    "calculator": calculator,
    "current_utc_time": current_utc_time,
}
