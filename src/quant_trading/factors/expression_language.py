"""Public contract for the restricted Factor expression language.

This module validates syntax only.  It never evaluates Python source and has no
market-data, GUI, storage, decision, risk, or execution dependency.
"""

from __future__ import annotations

import ast

from .errors import FactorDefinitionError


MARKET_FIELDS = frozenset(
    {"open", "high", "low", "close", "volume", "vwap", "trade_count"}
)
SERIES_FUNCTIONS = frozenset(
    {"latest", "lag", "mean", "sum", "minimum", "maximum"}
)
SCALAR_FUNCTIONS = frozenset({"absolute"})
ALLOWED_FUNCTIONS = SERIES_FUNCTIONS | SCALAR_FUNCTIONS
_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div)
_UNARYOPS = (ast.UAdd, ast.USub)


def parse_and_validate_expression(
    expression: str,
    parameter_names: tuple[str, ...] = (),
) -> ast.Expression:
    """Return a validated AST for the deliberately small numeric DSL."""

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise FactorDefinitionError(
            f"expression syntax is invalid: {exc.msg}"
        ) from exc
    nodes = tuple(ast.walk(tree))
    if len(nodes) > 100:
        raise FactorDefinitionError("expression is too complex")
    parameters = set(parameter_names)
    reserved = parameters & ALLOWED_FUNCTIONS
    if reserved:
        raise FactorDefinitionError(
            f"parameter name is reserved: {', '.join(sorted(reserved))}"
        )
    parents = {
        child: parent
        for parent in nodes
        for child in ast.iter_child_nodes(parent)
    }
    for node in nodes:
        if isinstance(node, (ast.Expression, ast.Load, ast.operator, ast.unaryop)):
            continue
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                raise FactorDefinitionError("boolean constants are not allowed")
            if isinstance(node.value, (int, float)):
                continue
            parent = parents.get(node)
            if (
                isinstance(node.value, str)
                and isinstance(parent, ast.Call)
                and parent.args
                and parent.args[0] is node
                and isinstance(parent.func, ast.Name)
                and parent.func.id in SERIES_FUNCTIONS
                and node.value in MARKET_FIELDS
            ):
                continue
            raise FactorDefinitionError(
                "string constants are allowed only as approved market fields"
            )
        if isinstance(node, ast.BinOp):
            if not isinstance(node.op, _BINOPS):
                raise FactorDefinitionError("only +, -, *, and / are allowed")
            continue
        if isinstance(node, ast.UnaryOp):
            if not isinstance(node.op, _UNARYOPS):
                raise FactorDefinitionError("only unary + and - are allowed")
            continue
        if isinstance(node, ast.Name):
            if node.id not in parameters and node.id not in ALLOWED_FUNCTIONS:
                raise FactorDefinitionError(f"unknown name: {node.id}")
            continue
        if isinstance(node, ast.Call):
            if (
                not isinstance(node.func, ast.Name)
                or node.func.id not in ALLOWED_FUNCTIONS
            ):
                raise FactorDefinitionError(
                    "only approved factor functions may be called"
                )
            if node.keywords:
                raise FactorDefinitionError("keyword arguments are not allowed")
            expected = 1 if node.func.id in {"latest", "absolute"} else 2
            if len(node.args) != expected:
                raise FactorDefinitionError(
                    f"{node.func.id} requires {expected} argument(s)"
                )
            continue
        raise FactorDefinitionError(
            f"expression construct is not allowed: {type(node).__name__}"
        )
    return tree
