"""Restricted Decimal-only sizing evaluation; account state remains read-only."""
import ast
from decimal import Decimal
from .definitions import SizingDefinition,SizingMode

def evaluate_sizing(definition: SizingDefinition,context):
    mode=definition.mode
    if mode is SizingMode.NONE:return None,()
    values={}
    if context is not None:
        for namespace,items in (("asset",context.asset_factors),("market",context.market_factors),("account",context.account_fields),("position",context.position_fields)):
            values.update({f"{namespace}.{x.name}":x.value for x in items})
    if mode is SizingMode.FIXED_USD:return definition.value,()
    field={SizingMode.PERCENT_AVAILABLE_CASH:"account.cash",SizingMode.PERCENT_EQUITY:"account.equity",SizingMode.PERCENT_POSITION_VALUE:"position.market_value",SizingMode.EXIT_ALL:"position.market_value"}.get(mode)
    if field is not None:
        if field not in values: raise ValueError(f"sizing requires {field}")
        amount=values[field] if mode is SizingMode.EXIT_ALL else values[field]*definition.value/Decimal(100)
        return _positive(amount),(field,)
    tree=ast.parse(definition.expression or "",mode="eval"); references=set()
    def evaluate(node):
        if isinstance(node,ast.Constant) and isinstance(node.value,(int,float)) and not isinstance(node.value,bool): return Decimal(str(node.value))
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            value=evaluate(node.operand); return value if isinstance(node.op,ast.UAdd) else -value
        if isinstance(node,ast.BinOp) and isinstance(node.op,(ast.Add,ast.Sub,ast.Mult,ast.Div)):
            left,right=evaluate(node.left),evaluate(node.right); return left+right if isinstance(node.op,ast.Add) else left-right if isinstance(node.op,ast.Sub) else left*right if isinstance(node.op,ast.Mult) else left/right
        if isinstance(node,ast.Attribute):
            parts=[]; current=node
            while isinstance(current,ast.Attribute): parts.append(current.attr); current=current.value
            if not isinstance(current,ast.Name): raise ValueError("invalid sizing reference")
            root=current.id; key=".".join((root,*reversed(parts)))
            if root not in ("asset","market","account","position") or key not in values: raise ValueError(f"unknown sizing reference: {key}")
            references.add(key); return values[key]
        raise ValueError("sizing expression supports only numbers, arithmetic, and approved references")
    return _positive(evaluate(tree.body)),tuple(sorted(references))
def _positive(value):
    if not value.is_finite() or value<=0: raise ValueError("sizing result must be a positive finite Decimal")
    return value
