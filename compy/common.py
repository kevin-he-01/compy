from enum import Enum
from functools import reduce
from dataclasses import dataclass, field
from typing import Iterable, List, TextIO, TypeVar

import compy.syntax

class UserError(Exception):
    pass

ID = str

@dataclass
class CompilerState:
    errors: List['CompileError'] = field(default_factory=list)
    def err(self, error: 'CompileError'):
        self.errors.append(error)

@dataclass
class DebugFlags:
    pipeline: bool
    asm: bool # *.nasm
    obj: bool # *.o

@dataclass
class CompilerInfo:
    src_path: str
    src_prefix: str # Ex. the part of the path without the suffix, Ex. 'file' for file.c, used to generate default names like file.o files etc.
    out_path: str
    debug_flags: DebugFlags
    stdout: TextIO
    stderr: TextIO
    state: CompilerState = field(default_factory=lambda: CompilerState())

    def print(self, msg: str = ''):
        print(msg, file=self.stdout)

    def error(self, msg: str):
        print(msg, file=self.stderr)

# A function to be compiled by the compiler 
@dataclass
class CompiledFunction:
    symbol: str
    body: 'compy.syntax.Scope'
    id: int
    stack_usage: int | None = None
    # id should originate from the function declaration node in the AST

class PrimType(Enum):
    INT = 0
    NONE = 1
    TYPE = 2

    def code(self) -> int:
        return self.value

@dataclass
class SourceSpan:
    lineno: int
    end_lineno: int | None
    col_offset: int
    end_col_offset: int | None
    # To make pretty prints smaller
    def __repr__(self) -> str:
        return f'"{self.lineno}:{self.col_offset}-{self.end_lineno}:{self.end_col_offset}"'

@dataclass
class CompileError(UserError):
    msg: str
    span: SourceSpan

    def __post_init__(self):
        super().__init__('Aborted due to compile error')

class IntegerOOB(CompileError):
    def __init__(self, val: int, span: SourceSpan):
        super().__init__(f'Integer constant {val} is out of bounds for type `int`', span)

class UnboundVarError(CompileError):
    def __init__(self, var: ID, span: SourceSpan):
        super().__init__(f"Unbound variable '{var}'", span)

class ImmutableVarError(CompileError):
    def __init__(self, var: ID, span: SourceSpan):
        super().__init__(f"Assignment to read-only variable (val) '{var}'", span)

class MutableClosureVarError(CompileError):
    def __init__(self, var: ID, span: SourceSpan):
        super().__init__(f"Variable defined outside closure must be immutable (val): '{var}' is mutable", span)

def report_error(info: CompilerInfo, code: str, ce: CompileError):
    lines = code.splitlines()
    span = ce.span
    error = info.error
    error(f'{info.src_path}:{span.lineno}:{span.col_offset + 1}: {ce.msg}')
    if span.lineno == span.end_lineno:
        line = lines[span.lineno-1]
        error(line)
        end = span.end_col_offset
        if end == None:
            end = len(line)
        error(' ' * span.col_offset + '^' * (end - span.col_offset))
    else:
        error('<Multiline error>')

T = TypeVar('T')
def concat(tss: Iterable[List[T]]) -> List[T]:
    emp: List[T] = []
    return reduce(lambda x, y: x + y, tss, emp)

O = TypeVar('O')
def unwrap(i: O | None, msg: str | None = None) -> O:
    if msg == None:
        assert i != None
    else:
        assert i != None, msg
    return i

MAIN = 'compy_main'
