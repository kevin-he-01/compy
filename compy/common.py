import sys
from dataclasses import dataclass, field
from typing import List

import compy.syntax

class UserError(Exception):
    pass

@dataclass
class CompilerState:
    errors: List['CompileError'] = field(default_factory=list)
    def err(self, error: 'CompileError'):
        self.errors.append(error)

@dataclass
class CompilerInfo:
    src_path: str
    src_prefix: str # Ex. the part of the path without the suffix, Ex. 'file' for file.c, used to generate default names like file.o files etc.
    out_path: str
    state: CompilerState = field(default_factory=lambda: CompilerState())

# next_function_id = 0

# def gen_function_id() -> int:
#     global next_function_id
#     next_function_id += 1
#     return next_function_id

# A function to be compiled by the compiler 
@dataclass
class CompiledFunction:
    symbol: str
    body: 'compy.syntax.Scope'
    id: int
    # id: int = field(default_factory=gen_function_id)

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

class UnboundVarError(CompileError):
    def __init__(self, var: 'compy.syntax.ID', span: SourceSpan):
        super().__init__(f"Unbound variable '{var}'", span)

class ImmutableVarError(CompileError):
    def __init__(self, var: 'compy.syntax.ID', span: SourceSpan):
        super().__init__(f"Assignment to read-only variable (val) '{var}'", span)

class MutableClosureVarError(CompileError):
    def __init__(self, var: 'compy.syntax.ID', span: SourceSpan):
        super().__init__(f"Variable defined outside closure must be immutable (val): '{var}' is mutable", span)

def report_error(info: CompilerInfo, code: str, ce: CompileError):
    lines = code.splitlines()
    span = ce.span
    print(f'{info.src_path}:{span.lineno}:{span.col_offset + 1}: {ce.msg}', file=sys.stderr)
    if span.lineno == span.end_lineno:
        line = lines[span.lineno-1]
        print(line)
        end = span.end_col_offset
        if end == None:
            end = len(line)
        print(' ' * span.col_offset + '^' * (end - span.col_offset), file=sys.stderr)
    else:
        print('<Multiline error>', file=sys.stderr)

MAIN = 'compy_main'
