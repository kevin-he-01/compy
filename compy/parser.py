import ast
from typing import List
from compy.syntax import SL, Expression, Integer, Name, Statement
from compy.common import CompileError, SourceSpan


def span_ast(a: ast.AST) -> SourceSpan:
    return SourceSpan(a.lineno, a.end_lineno, a.col_offset, a.end_col_offset)

def parse_expr(ex: ast.expr) -> Expression:
    span = span_ast(ex)
    match ex:
        case ast.Name(id=name):
            return Name(span=span, name=name)
        case ast.Constant(value=v):
            match v:
                case int(x):
                    return Integer(span=span, value=x)
                # TODO: booleans, strings, etc.
                case _:
                    raise CompileError(msg=f"Unknown literal {v}", span=span)
        case _:
            raise CompileError(msg="Unknown expression", span=span)

def parse_statement(s: ast.stmt) -> Statement:
    span = span_ast(s)
    match s:
        case ast.Expr(value=ex):
            return parse_expr(ex)
        case _:
            raise CompileError(msg="Unknown statement", span=span)

def parse_statements(ss: List[ast.stmt]) -> SL:
    return [parse_statement(s) for s in ss]

# Can throw SyntaxError's
def parse(code: str, filename: str = '<unknown>') -> SL:
    m = ast.parse(code, filename=filename)
    return parse_statements(m.body)
