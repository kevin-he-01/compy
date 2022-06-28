from dataclasses import dataclass
from compy.anf import IMM
from compy.asm import (AsmLine, Const, Label, MemOperand, Operand, Reg, Symbol, WordSize, add, call, cmp, extern,
                       global_, je, lea, mov, pop, push, ret, sub, jmp)
from compy.common import (MAIN, CompiledFunction, PrimType, SourceSpan, concat,
                          unwrap)
from compy.stack import op_stack
from compy.syntax import (IMM_EXPR, IMM_EXPRS, Assignment, BinOp, Binding, Boolean, EvalExpr, ExprScope, Expression, GetType, IfStmt, Integer,
                          Name, NewScope, NoOp, Prim1, Prim2, Print, Scope, Statement,
                          TypeLiteral, UnaryOp, Unit, VarInfo)

# TODO: make CODE iterable and migrate all the functions

CODE = list[AsmLine]

RVAL = Reg.RAX
RTYPE = Reg.RDX

# Registers used to pass arguments on the calling convention
RPARAMS = [Reg.RDI, Reg.RSI, Reg.RDX, Reg.RCX, Reg.R8, Reg.R9]

# Symbols
EXTRACT_BOOL = 'extract_bool'
PRINT_VARARGS = 'print_variadic'

@dataclass
class CodegenState:
    label_num: int = 0

    def new_label(self) -> str:
        self.label_num += 1
        return f'_compy_label_{self.label_num}'

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
    return Symbol(op.symbol())

def sym_binop(op: BinOp) -> Symbol:
    return Symbol(op.symbol())

def get_var_offset(name: Name) -> int:
    # TODO: when implementing closures, use effective offset from this call frame's stack
    return unwrap(name.info).get_stack_offset()

@dataclass
class AddrOf:
    mem_op: MemOperand

@dataclass
class Direct:
    op: Operand

ARG = Direct | AddrOf

def _imm_op(imm: IMM) -> MemOperand:
    match imm:
        case Name():
            return op_stack(get_var_offset(imm), size=WordSize.NONE)

def imm_op(imm: IMM_EXPR) -> MemOperand:
    assert isinstance(imm, IMM), 'Expected an immediate'
    return _imm_op(imm)

def imm2arg(imm: IMM_EXPR) -> ARG:
    return AddrOf(imm_op(imm))

def imms2args(imms: IMM_EXPRS) -> list[ARG]:
    return [imm2arg(imm) for imm in imms]

def load_into(reg: Reg, arg: ARG) -> AsmLine:
    match arg:
        case Direct(op):
            return mov(reg, op)
        case AddrOf(op):
            return lea(reg, op)

def call_runtime_func(sym_name: str, variadic: bool, args: list[ARG]) -> CODE:
    def iter_helper():
        code: CODE = [
            *(load_into(param_reg, arg) for param_reg, arg in zip(RPARAMS, args)),
            *([ mov(Reg.RAX, Const(0)) ] if variadic else []),
            call(Symbol(sym_name)),
        ]
        if len(args) > len(RPARAMS):
            extra_args = args[len(RPARAMS):]
            pad = bool(len(extra_args) % 2)
            if pad:
                yield sub(Reg.RSP, Const(8))
            yield from concat([
                load_into(Reg.RAX, arg),
                push(Reg.RAX)
            ] for arg in extra_args[::-1])
            # code = concat([
            #         load_into(Reg.RAX, arg),
            #         push(Reg.RAX)
            #     ] for arg in extra_args[::-1]) +\
            #     ([sub(Reg.RSP, Const(8))] if pad else []) +\
            #     code + [ add(Reg.RSP, (Const((len(extra_args) + pad) * 8))) ]
            yield from code
            yield add(Reg.RSP, (Const((len(extra_args) + pad) * 8)))
        else:
            yield from code
    return list(iter_helper())

# Compile into return registers
def compile_expr(ex: Expression) -> CODE:
    match ex:
        case Name():
            return read_var_at(get_var_offset(ex))
        case Integer(value=value):
            return [ mov(RVAL, Const(value)), mov(RTYPE, op_type(PrimType.INT)) ]
        case Boolean(value=value):
            return [ mov(RVAL, Const(int(value))), mov(RTYPE, op_type(PrimType.BOOL)) ]
        case TypeLiteral(ty=ty):
            return [ mov(RVAL, op_type(ty)), mov(RTYPE, op_type(PrimType.TYPE)) ]
        case GetType(ex=ex):
            return compile_expr(ex) + [ mov(RVAL, RTYPE), mov(RTYPE, op_type(PrimType.TYPE)) ]
        case Prim1(op=op, ex1=inside, span=SourceSpan(lineno=lineno)):
            return call_runtime_func(op.symbol(), False, [Direct(Const(lineno)), imm2arg(inside)])
        case Prim2(op=op, left=left, right=right, span=SourceSpan(lineno=lineno)):
            return call_runtime_func(op.symbol(), False, [Direct(Const(lineno)), *imms2args([left, right])])
        case Print(args=args, span=SourceSpan(lineno=lineno)):
            return call_runtime_func(PRINT_VARARGS, True, [Direct(Const(lineno)), Direct(Const(len(args))), *imms2args(args)])
        case Unit():
            return load_none()
        case ExprScope(scope=scope):
            return compile_scope(scope)
        case _: # pragma: no cover
            assert False, f'Unhandled expression: {type(ex)}'

def compile_if(stmt: IfStmt) -> CODE:
    label_false = _state.new_label()
    label_end = _state.new_label()
    op = imm_op(stmt.test)
    return [
        mov(RPARAMS[0], Const(stmt.span.lineno)),
        lea(RPARAMS[1], op),
        call(Symbol(EXTRACT_BOOL)),
        cmp(RVAL, Const(0)),
        je(Symbol(label_false)),
        *compile_scope(stmt.body),
        jmp(Symbol(label_end)),
        Label(label_false),
        *compile_scope(stmt.orelse),
        Label(label_end)
    ]

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
        # case IfStmt(test=test, body=body, orelse=orelse):
        case IfStmt():
            return compile_if(st)
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
    global _state
    _state = CodegenState()
    lines: CODE = [
        global_(MAIN),
        *(extern(op.symbol()) for op in UnaryOp),
        *(extern(op.symbol()) for op in BinOp),
        extern(EXTRACT_BOOL),
        extern(PRINT_VARARGS)
    ]
    for func in funcs:
        lines.extend(compile_func(func))
    return lines
