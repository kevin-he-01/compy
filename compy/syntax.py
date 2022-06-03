from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Generic, Iterable, List, TypeVar

import compy.common
import compy.keywords as kw

ID = str

# Tag information

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
    funcs: List[FuncInfo]

# Abstract AST types

@dataclass
class Node: # Base class of everything
    def children(self) -> Iterable['Node']:
        raise NotImplementedError

@dataclass
class Leaf(Node):
    def children(self) -> Iterable['Node']:
        return []

@dataclass
class Statement(Node):
    span: 'compy.common.SourceSpan'

@dataclass
class Expression(Statement):
    pass

# A scope can contain a list of statements

@dataclass
class Scope(Node):
    statements: List[Statement]
    info: ScopeInformation | None = None
    def children(self) -> Iterable['Node']:
        return self.statements

# Begin concrete AST statements

@dataclass
class Binding(Statement):
    mutable: bool
    name: ID
    init_val: Expression
    info: VarInfo | None = None
    def children(self) -> Iterable['Node']:
        return [self.init_val]

@dataclass
class Assignment(Statement):
    name: ID
    src: Expression
    target_span: 'compy.common.SourceSpan'
    info: INFO_ID | None = None
    def children(self) -> Iterable['Node']:
        return [self.src]

@dataclass
class NoOp(Leaf,Statement):
    pass

@dataclass
class NewScope(Statement):
    body: Scope
    def children(self) -> Iterable['Node']:
        return [self.body]

# Begin concrete AST expressions

@dataclass
class Name(Leaf,Expression):
    name: ID
    info: INFO_ID | None = None
    # TODO: add additional information on how to access this variable
    # Stack offset in the CURRENT function (can be different from info.stack_offset when it is a closure free variable)

@dataclass
class Integer(Leaf,Expression):
    value: int

class UnaryOp(Enum):
    NEGATE = auto()
    PRINT = auto() # For now, will make it a function later
    ADD1 = auto()
    SUB1 = auto()

KW_UNARY_OPS = {kw.PRINT: UnaryOp.PRINT, kw.ADD1: UnaryOp.ADD1, kw.SUB1: UnaryOp.SUB1}

@dataclass
class Prim1(Expression):
    op: UnaryOp
    ex1: Expression
    def children(self) -> List['Expression']:
        return [self.ex1]

# TODO: add function expr AST node that generates a unique ID upon instantiation
# TODO: add class that encloses Scope inside Expression to allow ANF-transforms/let-bindings

## AST Node walker, will aid in tagging nodes

C = TypeVar('C')

class NodeWalker(Generic[C]):
    # Overrider decide the order of traversal (pre-order, in-order, post-order, etc.)
    def walk(self, node: Node, ctx: C):
        for child in node.children():
            self.walk(child, ctx)
