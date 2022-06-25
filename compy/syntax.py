from dataclasses import dataclass, field, fields
from enum import Enum, auto
import sys
from typing import (Annotated, Any, Generic, Iterable, TypeAlias, TypeVar, get_args,
                    get_origin, get_type_hints)

import compy
import compy.common

ID: TypeAlias = 'compy.common.ID'

## Type annotations

@dataclass
class NeedImmediate: # Indicate a field need to be converted to an immediate during ANF phase
    pass

## Tag information

next_var_id = 0

def gen_var_id() -> int:
    global next_var_id
    next_var_id += 1
    return next_var_id

@dataclass
class VarInfo:
    # The originating function ID, used to decide whether an occurence is a closure free variable
    # or -1 for ANF variables that can never be free (never cross function boundaries)
    origin_function_id: int
    mutable: bool
    # Add type of variable, etc.
    # WARNING: this stack offset is relative to the frame of the orignating function
    stack_offset: int | None = None # From RBP
    # *** DEBUG INFORMATION ***
    var_id: int = field(default_factory=gen_var_id)

    def get_stack_offset(self, fail_msg: str = 'Stack offset not computed yet!'):
        return compy.common.unwrap(self.stack_offset, fail_msg)

@dataclass
class FuncInfo:
    symbol_name: str # Could be mangled
    # Add type of function, arity, etc. to aid in closure construction at the start of the scope

# Make functions declaration instead do this:
# val(func_name = <closure>)
# At the start of scope to unify variable and function handling
INFO_ID = VarInfo
# INFO_ID = VarInfo | FuncInfo

@dataclass
class ScopeInformation:
    funcs: list[FuncInfo]

## Abstract AST types

@dataclass
class Node: # Base class of everythingd
    def child_fields(self) -> Iterable[str]:
        return child_fields(type(self))
    def children(self) -> Iterable['Node']:
        for fld in self.child_fields():
            val: Iterable[Node] | Node = getattr(self, fld)
            match val:
                case Node():
                    yield val
                case _:
                    yield from val

FIELDS_CACHE: dict[type[Node], list[str]] = dict()

_TAB = ' ' * 4

# Return cached results
def child_fields(clz: type[Node]) -> Iterable[str]:
    if clz not in FIELDS_CACHE:
        FIELDS_CACHE[clz] = list(_child_fields(clz))
        if compy.debug_ast_children: # pragma: no cover
            flds = FIELDS_CACHE[clz]
            print(f'class {clz.__name__}: # Children list\n{_TAB}' +
                (f'\n{_TAB}'.join(flds) if flds else 'pass # [Leaf]'), file=sys.stderr)
    return FIELDS_CACHE[clz]

# Uncached version
def _child_fields(clz: type[Node]) -> Iterable[str]:
    # Note: the order of declaring fields inside class is significant
    # when determining traversal order (consequently evaluation order in ANF)
    def report_unknown_type(field_name: str, ty: Any, extra_msg: str = ''):
        if compy.debug_ast_children: # pragma: no cover
            print(f'WARNING: Unknown type annotation on {clz.__name__}.{field_name}: {repr(ty)}{extra_msg}')
    types = get_type_hints(clz)
    for field in fields(clz):
        name = field.name
        ty = types[name]
        match ty:
            case type():
                if get_origin(ty) == list:
                    (inner_type,) = get_args(ty)
                    if not isinstance(inner_type, type):
                        report_unknown_type(name, inner_type, extra_msg=' (Inside list[...])')
                        continue
                    ty = inner_type
                if issubclass(ty, Node):
                    yield name
            case _:
                report_unknown_type(name, ty)
                pass

@dataclass
class Statement(Node):
    span: 'compy.common.SourceSpan'

@dataclass
class Expression(Node):
    span: 'compy.common.SourceSpan'

@dataclass
class EvalExpr(Statement): # Evaluate an expression for its side effects only, ignoring its value
    expr: Expression

IMM_EXPR = Annotated[Expression, NeedImmediate()]

## A scope can contain a list of statements

@dataclass
class Scope(Node):
    statements: list[Statement]
    info: ScopeInformation | None = None

## Begin concrete AST statements

@dataclass
class Binding(Statement):
    mutable: bool
    name: ID
    init_val: Expression
    info: VarInfo | None = None

@dataclass
class Assignment(Statement):
    name: ID
    src: Expression
    target_span: 'compy.common.SourceSpan'
    info: INFO_ID | None = None

@dataclass
class NoOp(Statement):
    pass

@dataclass
class NewScope(Statement):
    body: Scope

## Begin concrete AST expressions

@dataclass
class Name(Expression):
    name: ID
    info: INFO_ID | None = None
    # TODO: add additional information on how to access this variable
    # Stack offset in the CURRENT function (can be different from info.stack_offset when it is a closure free variable)

@dataclass
class Integer(Expression):
    value: int

@dataclass
class TypeLiteral(Expression):
    ty: 'compy.common.PrimType'

@dataclass
class Unit(Expression): # The only instance of 'None'
    pass

@dataclass
class GetType(Expression): # Could be a Prim1, but do not need ex to be immediate for ANF
    ex: Expression

class UnaryOp(Enum):
    NEGATE = auto()
    PRINT = auto() # For now, will make it a function later
    ADD1 = auto()
    SUB1 = auto()

@dataclass
class Prim1(Expression):
    op: UnaryOp
    ex1: IMM_EXPR

@dataclass
class ExprScope(Expression):
    scope: Scope

def mk_exprscope(span: 'compy.common.SourceSpan', ss: list[Statement], expr: Expression):
    return ExprScope(span=span, scope=Scope(ss + [EvalExpr(span=expr.span, expr=expr)]))

# TODO: add function expr AST node that generates a unique ID upon instantiation
# TODO: add class that encloses Scope inside Expression to allow ANF-transforms/let-bindings

## AST Node walker, will aid in tagging nodes

C = TypeVar('C')

class NodeWalker(Generic[C]):
    # Overrider decide the order of traversal (pre-order, in-order, post-order, etc.)
    def walk(self, node: Node, ctx: C):
        for child in node.children():
            self.walk(child, ctx)

## Users should import ID from common, not syntax since this is a foward reference
del ID
