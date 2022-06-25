from compy.anf import IMM
from compy.asm import (AsmLine, Const, Label, Operand, Reg, Symbol, WordSize, add, call, extern,
                       global_, lea, mov, pop, push, ret, sub)
from compy.common import (MAIN, CompiledFunction, PrimType, SourceSpan, concat,
                          unwrap)
from compy.stack import op_stack
from compy.syntax import (IMM_EXPR, Assignment, Binding, EvalExpr, ExprScope, Expression, GetType, Integer,
                          Name, NewScope, NoOp, Prim1, Scope, Statement,
                          TypeLiteral, UnaryOp, Unit, VarInfo)

CODE = list[AsmLine]

RVAL = Reg.RAX
RTYPE = Reg.RDX

# Registers used to pass arguments on the calling convention
RPARAMS = [Reg.RDI, Reg.RSI, Reg.RDX, Reg.RCX, Reg.R8, Reg.R9]

# External functions
PRINT = 'print'
NEGATE = 'negate'
ADD1 = 'add1'
SUB1 = 'sub1'

def op_type(ty: PrimType):
    return Const(ty.code())

def op_var_val(stack_offset: int):
    return op_stack(stack_offset, offset=0)
def op_var_type(stack_offset: int):
    return op_stack(stack_offset, offset=8)

# Assign from return registers to variable
def assign(info: VarInfo) -> CODE:
    return [ mov(op_var_val(info.get_stack_offset()), RVAL), mov(op_var_type(info.get_stack_offset()), RTYPE) ]
# Read variable content into return registers
def read_var_at(stack_offset: int) -> CODE:
    return [ mov(RVAL, op_var_val(stack_offset)), mov(RTYPE, op_var_type(stack_offset)) ]
# Load a `None` value into return registers
def load_none() -> CODE:
    return [ mov(RVAL, Const(0)), mov(RTYPE, op_type(PrimType.NONE)) ]

def sym_op(op: UnaryOp) -> Symbol:
    match op:
        case UnaryOp.NEGATE:
            return Symbol(NEGATE)
        case UnaryOp.PRINT:
            return Symbol(PRINT)
        case UnaryOp.ADD1:
            return Symbol(ADD1)
        case UnaryOp.SUB1:
            return Symbol(SUB1)

def get_var_offset(name: Name) -> int:
    # TODO: when implementing closures, use effective offset from this call frame's stack
    return unwrap(name.info).get_stack_offset()

def _imm_op(imm: IMM) -> Operand:
    match imm:
        case Name():
            return op_stack(get_var_offset(imm), size=WordSize.NONE)

def imm_op(imm: IMM_EXPR) -> Operand:
    assert isinstance(imm, IMM), 'Expected an immediate'
    return _imm_op(imm)

# Compile into return registers
def compile_expr(ex: Expression) -> CODE:
    match ex:
        case Name():
            return read_var_at(get_var_offset(ex))
        case Integer(value=value):
            return [ mov(RVAL, Const(value)), mov(RTYPE, op_type(PrimType.INT)) ]
        case TypeLiteral(ty=ty):
            return [ mov(RVAL, op_type(ty)), mov(RTYPE, op_type(PrimType.TYPE)) ]
        case GetType(ex=ex):
            return compile_expr(ex) + [ mov(RVAL, RTYPE), mov(RTYPE, op_type(PrimType.TYPE)) ]
        case Prim1(op=op, ex1=inside, span=SourceSpan(lineno=lineno)):
            return [ mov(RPARAMS[0], Const(lineno)), lea(RPARAMS[1], imm_op(inside)), call(sym_op(op)) ]
        case Unit():
            return load_none()
        case ExprScope(scope=scope):
            return compile_scope(scope)
        case _: # pragma: no cover
            assert False, f'Unhandled expression: {type(ex)}'

# TODO: accept return label as second arg for compile_scope and compile_statement
def compile_statement(st: Statement) -> CODE:
    match st:
        case EvalExpr(expr=ex):
            return compile_expr(ex)
        case Assignment(info=info, src=src_expr):
            return compile_expr(src_expr) + assign(unwrap(info))
        case Binding(info=info, init_val=src_expr):
            return compile_expr(src_expr) + assign(unwrap(info))
        case NoOp():
            return []
        case NewScope(body=scope):
            return compile_scope(scope)
        case _: # pragma: no cover
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

def compile_prog(funcs: list[CompiledFunction]) -> CODE:
    lines: CODE = [
        global_(MAIN),
        extern(PRINT),
        extern(NEGATE),
        extern(ADD1),
        extern(SUB1),
    ]
    for func in funcs:
        lines.extend(compile_func(func))
    return lines
