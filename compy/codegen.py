from typing import List
from compy.asm import AsmLine, Const, Label, Reg, Symbol, add, call, extern, global_, mov, neg, push, ret, sub, pop
from compy.common import MAIN, CompiledFunction, concat, unwrap
from compy.stack import op_stack
from compy.syntax import Assignment, Binding, Expression, Integer, Name, NewScope, NoOp, Prim1, Scope, Statement, UnaryOp, Unit, VarInfo


CODE = List[AsmLine]

RVAL = Reg.RAX
RTYPE = Reg.RDX # TODO: use this as type

# Registers used to pass arguments on the calling convention
RPARAMS = [Reg.RDI, Reg.RSI, Reg.RDX, Reg.RCX, Reg.R8, Reg.R9]

# External functions
PRINT_SIGNED_INT = 'print_signed_int'

# TODO: For assign and read_var, move to both RAX, RDX (abstract them away in constant as well!), and create helper variable of retrieving op_stack for both type and value
# Assign from return registers to variable
def assign(info: VarInfo) -> CODE:
    return [ mov(op_stack(info.get_stack_offset()), RVAL) ]
def read_var_at(stack_offset: int) -> CODE:
    return [ mov(RVAL, op_stack(stack_offset)) ]
def load_none() -> CODE:
    # For now, let None be 0
    return [ mov(RVAL, Const(0)) ]

# Compile into return registers
def compile_expr(ex: Expression) -> CODE:
    match ex:
        case Name(info=info):
            # TODO: when implementing closures, use effective offset from this call frame's stack
            return read_var_at(unwrap(info).get_stack_offset())
        case Integer(value=value):
            return [ mov(RVAL, Const(value)) ]
        case Prim1(op=UnaryOp.NEGATE, ex1=inside):
            return compile_expr(inside) + [ neg(RVAL) ]
        case Prim1(op=UnaryOp.PRINT, ex1=inside):
            return compile_expr(inside) + [ mov(RPARAMS[0], RVAL), call(Symbol(PRINT_SIGNED_INT)) ] + load_none()
        case Prim1(op=UnaryOp.ADD1, ex1=inside):
            return compile_expr(inside) + [ add(RVAL, Const(1)) ]
        case Prim1(op=UnaryOp.SUB1, ex1=inside):
            return compile_expr(inside) + [ sub(RVAL, Const(1)) ]
        case Unit():
            return load_none()
        case _:
            assert False, f'Unhandled expression: {type(ex)}'

# TODO: accept return label as second arg for compile_scope and compile_statement
def compile_statement(st: Statement) -> CODE:
    match st:
        case Expression():
            return compile_expr(st)
        case Assignment(info=info, src=src_expr):
            return compile_expr(src_expr) + assign(unwrap(info))
        case Binding(info=info, init_val=src_expr):
            return compile_expr(src_expr) + assign(unwrap(info))
        case NoOp():
            return []
        case NewScope(body=scope):
            return compile_scope(scope)
        case _:
            assert False, f'Unhandled statement: {type(st)}'

def compile_scope(scope: Scope) -> CODE:
    # TODO: initialize functions as closures
    return concat(compile_statement(st) for st in scope.statements)

def compile_func(func: CompiledFunction) -> CODE:
    stack_space = unwrap(func.stack_usage, 'Stack space not computed before compile')
    return [
        Label(func.symbol),
        push(Reg.RBP),
        mov(Reg.RBP, Reg.RSP),
        sub(Reg.RSP, Const(stack_space)),
        # TODO: pass return label as second arg, with None if compiling outside declaration where return is not allowed (should handle this in checker)
        *compile_scope(func.body),
        *load_none(), # 'return None' when slipping off the end of function
        # TODO: allocate and insert a "function end" label here (generate label from a mutable state object) to allow returns
        add(Reg.RSP, Const(stack_space)),
        pop(Reg.RBP),
        ret(),
    ]

def compile_prog(funcs: List[CompiledFunction]) -> CODE:
    lines: CODE = [
        global_(MAIN),
        extern(PRINT_SIGNED_INT),
    ]
    for func in funcs:
        lines.extend(compile_func(func))
    return lines
