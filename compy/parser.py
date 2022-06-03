import ast
from typing import List
from compy.syntax import ID, KW_UNARY_OPS, Assignment, Binding, Expression, Integer, NewScope, NoOp, Prim1, Scope, Statement
import compy.syntax as syn
from compy.common import CompileError, SourceSpan
import compy.keywords as kw

def validate_name(span: SourceSpan, name: ID):
    if kw.is_keyword(name):
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
            return syn.Name(span=span, name=name)
        case ast.Constant(value=v):
            match v:
                case int(x):
                    return Integer(span=span, value=x)
                # TODO: booleans, strings, etc.
                case _:
                    raise CompileError(msg=f"Unknown literal {v}", span=span)
        case ast.Call(func=ast.Name(id=(kw.PRINT | kw.ADD1 | kw.SUB1 as func)), args=[ex1]):
            return Prim1(span=span, op=KW_UNARY_OPS[func], ex1=parse_expr(ex1))
        case _:
            raise CompileError(msg="Unknown expression", span=span)

def parse_assignment(span_stmt: SourceSpan, target: ast.expr, src: ast.expr) -> Statement:
    match target:
        case ast.Name(id=name):
            validate_name_ast(target)
            return Assignment(span=span_stmt, name=name, target_span=span_ast(target), src=parse_expr(src))
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
        case ast.Pass():
            return NoOp(span=span)
        case ast.With(items=[ast.withitem(context_expr=ast.Name(id=kw.UNDERSCORE))], body=stmts):
            return NewScope(body=parse_statements(stmts),span=span)
        case _:
            print(ast.dump(s, indent=2))
            raise CompileError(msg="Unknown statement", span=span)

def parse_statements(ss: List[ast.stmt]) -> Scope:
    return Scope([parse_statement(s) for s in ss])

# Can throw SyntaxError's
def parse(code: str, filename: str = '<unknown>') -> Scope:
    m = ast.parse(code, filename=filename)
    return parse_statements(m.body)
