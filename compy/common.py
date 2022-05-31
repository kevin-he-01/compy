import sys
from dataclasses import dataclass

@dataclass
class CompilerInfo:
    src_path: str
    src_prefix: str # Ex. the part of the path without the suffix, Ex. 'file' for file.c, used to generate default names like file.o files etc.
    out_path: str

@dataclass
class SourceSpan:
    lineno: int
    end_lineno: int | None
    col_offset: int
    end_col_offset: int | None

@dataclass
class CompileError(Exception):
    msg: str
    span: SourceSpan

    def __post_init__(self):
        super().__init__('Aborted due to compile error')

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
