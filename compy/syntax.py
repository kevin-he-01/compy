from dataclasses import dataclass
from enum import Enum
from typing import List

from compy.common import SourceSpan

ID = str

# Abstract AST types

@dataclass
class Statement:
    span: SourceSpan

@dataclass
class Expression(Statement):
    pass

# Begin concrete AST statements

@dataclass
class Binding(Statement):
    mutable: bool
    name: ID
    init_val: Expression

@dataclass
class Assignment(Statement):
    name: ID
    src: Expression

# Begin concrete AST expressions

@dataclass
class Name(Expression):
    name: ID

@dataclass
class Integer(Expression):
    value: int

class UnaryOp(Enum):
    NEGATE = 0
    PRINT = 1 # For now, will make it a function later
    ADD1 = 2
    SUB1 = 3

@dataclass
class Prim1(Expression):
    op: UnaryOp
    ex1: Expression

SL = List[Statement]
