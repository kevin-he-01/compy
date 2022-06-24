import ast
from typing import Iterable

import compy.keywords as kw
import compy.syntax as syn
from compy.common import ID, CompileError, SourceSpan


def validate_name(span: SourceSpan, name: ID):
    if kw.is_keyword(name):
        raise CompileError(msg=f"{name} is a reserved keyword", span=span)

def validate_name_ast(name: ast.Name):
    validate_name(span_ast(name), name.id)

def span_ast(a: ast.AST) -> SourceSpan:
    return SourceSpan(a.lineno, a.end_lineno, a.col_offset, a.end_col_offset)

def parse_let(span: SourceSpan, binds: list[ast.expr], body: ast.expr) -> syn.ExprScope:
    def iter_args() -> Iterable[syn.Statement]:
        for arg in binds:
            span_arg = span_ast(arg)
            match arg:
                case ast.NamedExpr(target=ast.Name(id=id_name, ctx=ast.Store()) as name, value=src):
                    validate_name_ast(name)
                    yield syn.Binding(span=span_arg, mutable=False, name=id_name, init_val=parse_expr(src))
                case _:
                    raise CompileError(msg="Bindings before the body must be of the form x := <expr>", span=span_arg)
    return syn.mk_exprscope(span, list(iter_args()), parse_expr(body))

def parse_expr(ex: ast.expr) -> syn.Expression:
    span = span_ast(ex)
    match ex:
        case ast.Name(id=name):
            if kw.is_type_name(name):
                return syn.TypeLiteral(span=span, ty=kw.name_to_type(name))
            else:
                validate_name_ast(ex)
                return syn.Name(span=span, name=name)
        case ast.Constant(value=v):
            match v:
                case None:
                    return syn.Unit(span=span)
                case int(x):
                    return syn.Integer(span=span, value=x)
                # TODO: booleans, strings, etc.
                case _:
                    raise CompileError(msg=f"Unknown literal {v}", span=span)
        case ast.Call(func=ast.Name(id=kw.TYPE), args=[ex1], keywords=[]):
            return syn.GetType(span=span, ex=parse_expr(ex1))
        case ast.Call(func=ast.Name(id=(kw.PRINT | kw.ADD1 | kw.SUB1 as func)), args=[ex1], keywords=[]):
            return syn.Prim1(span=span, op=kw.KW_UNARY_OPS[func], ex1=parse_expr(ex1))
        case ast.Call(func=ast.Name(id=kw.LET), args=[*binds, body], keywords=[]):
            return parse_let(span, binds, body)
        case ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=int(x))):
            return syn.Integer(span=span, value=-x)
        case ast.UnaryOp(op=ast.USub(), operand=ex1):
            return syn.Prim1(span=span, op=syn.UnaryOp.NEGATE, ex1=parse_expr(ex1))
        case _:
            raise CompileError(msg="Unknown expression", span=span)

def parse_assignment(span_stmt: SourceSpan, target: ast.expr, src: ast.expr) -> syn.Statement:
    match target:
        case ast.Name(id=name):
            validate_name_ast(target)
            return syn.Assignment(span=span_stmt, name=name, target_span=span_ast(target), src=parse_expr(src))
        # TODO: assign to list elements, destructuring of tuples, etc.
        case _:
            raise CompileError(msg="Cannot assign to this target", span=span_ast(target))

def parse_stmt_expr(span_stmt: SourceSpan, ex: ast.expr) -> syn.Statement:
    match ex:
        case ast.Call(func=ast.Name(id=(kw.VAL | kw.VAR as ty)), args=[], keywords=[ast.keyword(arg=name, value=ex) as keyword]):
            mutable = ty == kw.VAR
            if name is None:
                raise CompileError('Bad val/var binding', span_stmt)
            validate_name(span_ast(keyword), name)
            return syn.Binding(span=span_stmt, mutable=mutable, name=name, init_val=parse_expr(ex))
        case _:
            return syn.EvalExpr(span=span_stmt, expr=parse_expr(ex))

def parse_statement(s: ast.stmt) -> syn.Statement:
    span = span_ast(s)
    match s:
        case ast.Expr(value=ex):
            return parse_stmt_expr(span, ex)
        case ast.Assign(targets=[x], value=v):
            return parse_assignment(span, x, v)
        case ast.Pass():
            return syn.NoOp(span=span)
        case ast.With(items=[ast.withitem(context_expr=ast.Name(id=kw.UNDERSCORE))], body=stmts):
            return syn.NewScope(body=parse_statements(stmts),span=span)
        case _:
            print(ast.dump(s, indent=2))
            raise CompileError(msg="Unknown statement", span=span)

def parse_statements(ss: list[ast.stmt]) -> syn.Scope:
    return syn.Scope([parse_statement(s) for s in ss])

# Can throw SyntaxError's
def parse(code: str, filename: str = '<unknown>') -> syn.Scope:
    m = ast.parse(code, filename=filename)
    return parse_statements(m.body)
