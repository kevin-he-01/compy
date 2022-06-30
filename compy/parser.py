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

def convert_binop(span: SourceSpan, op: ast.operator) -> syn.BinOp:
    match op:
        case ast.Add():
            return syn.BinOp.ADD
        case ast.Sub():
            return syn.BinOp.SUB
        case ast.Mult():
            return syn.BinOp.MUL
        case ast.Div():
            return syn.BinOp.DIV
        case ast.Mod():
            return syn.BinOp.MOD
        case _: # pragma: no cover
            raise CompileError('Unsupported binary operation', span)

def convert_cmpop(span: SourceSpan, op: ast.cmpop) -> tuple[syn.BinOp, bool]:
    match op:
        case ast.Is():
            return syn.BinOp.IS, False
        case ast.Eq():
            return syn.BinOp.EQ, False
        case ast.IsNot():
            return syn.BinOp.IS, True
        case ast.NotEq():
            return syn.BinOp.EQ, True
        case ast.LtE():
            return syn.BinOp.LE, False 
        case ast.Lt():
            return syn.BinOp.LT, False 
        case ast.GtE():
            return syn.BinOp.GE, False 
        case ast.Gt():
            return syn.BinOp.GT, False 
        case _: # pragma: no cover
            raise CompileError('Unsupported comparison operation', span)

def convert_un_op(span: SourceSpan, op: ast.unaryop) -> syn.UnaryOp:
    match op:
        case ast.USub():
            return syn.UnaryOp.NEGATE
        case ast.Not():
            return syn.UnaryOp.NOT
        case _: # pragma: no cover
            raise CompileError('Unsupported unary operation', span)

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
                case bool(x):
                    return syn.Boolean(span=span, value=x)
                case int(x):
                    return syn.Integer(span=span, value=x)
                case str(s):
                    return syn.StringLiteral(span=span, content=s)
                # TODO: bytes
                case _: # pragma: no cover
                    raise CompileError(msg=f"Unknown literal {v}", span=span)
        case ast.Call(func=ast.Name(id=kw.TYPE), args=[ex1], keywords=[]):
            return syn.GetType(span=span, ex=parse_expr(ex1))
        case ast.Call(func=ast.Name(id=kw.PRINT), args=exs, keywords=[]):
            return syn.Print(span=span, args=[parse_expr(ex) for ex in exs])
        case ast.Call(func=ast.Name(id=kw.INPUT), args=exs, keywords=[]):
            return syn.Input(span=span, args=[parse_expr(ex) for ex in exs])
        case ast.Call(func=ast.Name(id=(kw.ADD1 | kw.SUB1 as func)), args=[ex1], keywords=[]):
            return syn.Prim1(span=span, op=kw.KW_UNARY_OPS[func], ex1=parse_expr(ex1))
        case ast.Call(func=ast.Name(id=kw.LET), args=[*binds, body], keywords=[]):
            return parse_let(span, binds, body)
        case ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=int(x))):
            return syn.Integer(span=span, value=-x)
        case ast.UnaryOp(op=op, operand=ex1):
            return syn.Prim1(span=span, op=convert_un_op(span, op), ex1=parse_expr(ex1))
        case ast.BinOp(op=op, left=left, right=right):
            return syn.Prim2(span=span, op=convert_binop(span, op), left=parse_expr(left), right=parse_expr(right))
        case ast.Compare(left=left, ops=[cmp_op], comparators=[right]):
            op, invert = convert_cmpop(span, cmp_op)
            base = syn.Prim2(span=span, op=op, left=parse_expr(left), right=parse_expr(right))
            return syn.Prim1(span, syn.UnaryOp.NOT, base) if invert else base
        case ast.Compare():
            raise CompileError(msg="Cannot chain multiple comparisons like in Python", span=span)
        case _: # pragma: no cover
            raise CompileError(msg="Unknown expression", span=span)

def parse_assignment(span_stmt: SourceSpan, target: ast.expr, src: ast.expr) -> syn.Statement:
    match target:
        case ast.Name(id=name):
            validate_name_ast(target)
            return syn.Assignment(span=span_stmt, name=name, target_span=span_ast(target), src=parse_expr(src))
        # TODO: assign to list elements, destructuring of tuples, etc.
        case _: # pragma: no cover
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
        case ast.If(test=test, body=body, orelse=orelse):
            return syn.IfStmt(span=span, test=parse_expr(test), body=parse_statements(body), orelse=parse_statements(orelse))
        case _: # pragma: no cover
            print(ast.dump(s, indent=2))
            raise CompileError(msg="Unknown statement", span=span)

def parse_statements(ss: list[ast.stmt]) -> syn.Scope:
    return syn.Scope([parse_statement(s) for s in ss])

# Can throw SyntaxError's
def parse(code: str, filename: str = '<unknown>') -> syn.Scope:
    m = ast.parse(code, filename=filename)
    return parse_statements(m.body)
