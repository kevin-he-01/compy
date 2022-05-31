import ast
from typing import List
from compy.syntax import ID, SL, Assignment, Binding, Expression, Integer, Name, Statement
from compy.common import CompileError, SourceSpan
import compy.keywords as kw

def validate_name(span: SourceSpan, name: ID):
    if name in kw.ALL_KEYWORDS:
        raise CompileError(msg=f"{name} is a reserved keyword", span=span)

def validate_name_ast(name: ast.Name):
    validate_name(span_ast(name), name.id)

def span_ast(a: ast.AST) -> SourceSpan:
    return SourceSpan(a.lineno, a.end_lineno, a.col_offset, a.end_col_offset)

def parse_expr(ex: ast.expr) -> Expression:
    span = span_ast(ex)
    match ex:
        case ast.Name(id=name):
            validate_name_ast(ex)
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

def parse_assignment(span_stmt: SourceSpan, target: ast.expr, src: ast.expr) -> Statement:
    match target:
        case ast.Name(id=name):
            validate_name_ast(target)
            return Assignment(span=span_stmt, name=name, src=parse_expr(src))
        # TODO: assign to list elements, destructuring of tuples, etc.
        case _:
            raise CompileError(msg="Cannot assign to this target", span=span_ast(target))


def parse_stmt_expr(span_stmt: SourceSpan, ex: ast.expr) -> Statement:
    match ex:
        case ast.Call(func=ast.Name(id=(kw.VAL | kw.VAR as ty)), args=[], keywords=[ast.keyword(arg=name, value=ex) as keyword]):
            mutable = ty == kw.VAR
            if name == None:
                raise CompileError('Bad val/var binding', span_stmt)
            validate_name(span_ast(keyword), name)
            return Binding(span_stmt, mutable=mutable, name=name, init_val=parse_expr(ex))
        case _:
            return parse_expr(ex)

def parse_statement(s: ast.stmt) -> Statement:
    span = span_ast(s)
    match s:
        case ast.Expr(value=ex):
            return parse_stmt_expr(span, ex)
        case ast.Assign(targets=[x], value=v):
            return parse_assignment(span, x, v)
        case _:
            raise CompileError(msg="Unknown statement", span=span)

def parse_statements(ss: List[ast.stmt]) -> SL:
    return [parse_statement(s) for s in ss]

# Can throw SyntaxError's
def parse(code: str, filename: str = '<unknown>') -> SL:
    m = ast.parse(code, filename=filename)
    return parse_statements(m.body)
