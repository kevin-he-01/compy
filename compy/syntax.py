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

# Begin concrete AST nodes

@dataclass
class Name(Expression):
    name: ID

@dataclass
class Integer(Expression):
    value: int

class UnaryOp(Enum):
    ADD1 = 1
    SUB1 = 2

@dataclass
class Prim1(Expression):
    op: UnaryOp

SL = List[Statement]
