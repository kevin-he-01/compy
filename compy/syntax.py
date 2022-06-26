from dataclasses import dataclass, field, fields
from enum import Enum
import sys
from typing import (Annotated, Any, Generic, Iterable, TypeAlias, TypeVar, get_args,
                    get_origin, get_type_hints)

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
    funcs: list[FuncInfo] = field(default_factory=list)

## Abstract AST types

@dataclass
class Node: # Base class of everythingd
    def child_fields(self) -> Iterable['Field']:
        for fld_name, fld_type, imm in child_fields(type(self)):
            yield Field(obj=self, attr_name=fld_name, ty=fld_type, need_imm=imm)
    def children(self) -> Iterable['Node']:
        for fld in self.child_fields():
            val = fld.get()
            match val:
                case Node():
                    yield val
                case _:
                    yield from val


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

## AST Children detection

@dataclass
class Field:
    obj: Node
    attr_name: str
    ty: type
    need_imm: bool

    def get(self) -> Iterable[Node] | Node:
        return getattr(self.obj, self.attr_name)

    # def get_as_expr(self) -> Iterable[Expression] | Expression:
    #     assert self.need_imm
    #     return getattr(self.obj, self.attr_name)
    
    def set(self, value: Iterable[Node] | Node):
        match value:
            case Node():
                assert get_origin(self.ty) != list, 'Setting non-list to list field'
                assert isinstance(value, self.ty), 'Type mismatch on singular item assignment'
                setattr(self.obj, self.attr_name, value)
            case _:
                assert get_origin(self.ty) == list, 'Setting list to non-list field'
                (inner_type,) = get_args(self.ty)
                vals: list[Any] = []
                for val in value:
                    assert isinstance(val, inner_type), 'Type mismatch on plural item assignment'
                    vals.append(val)
                setattr(self.obj, self.attr_name, vals)

CLASS_FIELD = tuple[str, type, bool]

FIELDS_CACHE: dict[type[Node], list[CLASS_FIELD]] = dict()

_TAB = ' ' * 4

debug_ast_children: bool = False

# Return cached results
def child_fields(clz: type[Node]) -> Iterable[CLASS_FIELD]:
    if clz not in FIELDS_CACHE:
        FIELDS_CACHE[clz] = list(_child_fields(clz))
        if debug_ast_children: # pragma: no cover
            flds = FIELDS_CACHE[clz]
            print(f'class {clz.__name__}: # Children list\n{_TAB}' +
                (f'\n{_TAB}'.join(f'{name}: {repr(ty)}{" # Immediate" * imm}' for name, ty, imm in flds) if flds else 'pass # [Leaf]'), file=sys.stderr)
    return FIELDS_CACHE[clz]

# Uncached version
def _child_fields(clz: type[Node]) -> Iterable[CLASS_FIELD]:
    # Note: the order of declaring fields inside class is significant
    # when determining traversal order (consequently evaluation order in ANF)
    def report_unknown_type(field_name: str, ty: Any, extra_msg: str = ''):
        if debug_ast_children: # pragma: no cover
            print(f'WARNING: Unknown type annotation on {clz.__name__}.{field_name}: {repr(ty)}{extra_msg}')
    types = get_type_hints(clz)
    types_annot = get_type_hints(clz, include_extras=True)
    for field in fields(clz):
        name = field.name
        ty = types[name]
        full_type = types_annot[name]
        match ty:
            case type():
                current_ty = ty
                if get_origin(ty) == list:
                    (inner_type,) = get_args(ty)
                    if not isinstance(inner_type, type): # pragma: no cover
                        report_unknown_type(name, inner_type, extra_msg=' (Inside list[...])')
                        continue
                    current_ty = inner_type
                if issubclass(current_ty, Node):
                    imm = bool(get_origin(full_type) == Annotated) and NeedImmediate() in get_args(full_type)
                    if imm:
                        assert issubclass(current_ty, Expression), 'Cannot make immediate a non-expression'
                    yield name, ty, imm
            case _:
                report_unknown_type(name, ty)
                pass

## A scope contains a list of statements

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

@dataclass
class IfStmt(Statement):
    test: IMM_EXPR
    body: Scope
    orelse: Scope

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
class Boolean(Expression):
    value: bool

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
    NEGATE = 'negate'
    PRINT = 'print' # For now, will make it a function later
    ADD1 = 'add1'
    SUB1 = 'sub1'
    NOT = 'boolean_not'

    # Runtime call symbol
    def symbol(self) -> str:
        return self.value

class BinOp(Enum):
    ADD = 'add'
    SUB = 'sub'
    MUL = 'mul'
    DIV = 'div'
    MOD = 'mod'
    IS = 'is_identical'
    EQ = 'is_eq'
    LT = 'is_lt'
    GT = 'is_gt'
    LE = 'is_le'
    GE = 'is_ge'

    # Runtime call symbol
    def symbol(self) -> str:
        return self.value

@dataclass
class Prim1(Expression):
    op: UnaryOp
    ex1: IMM_EXPR

@dataclass
class Prim2(Expression):
    op: BinOp
    left: IMM_EXPR
    right: IMM_EXPR

@dataclass
class ExprScope(Expression):
    scope: Scope

def mk_exprscope(span: 'compy.common.SourceSpan', ss: list[Statement], expr: Expression, info: ScopeInformation | None = None) -> ExprScope:
    return ExprScope(span=span, scope=Scope(ss + [EvalExpr(span=expr.span, expr=expr)], info=info))

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
