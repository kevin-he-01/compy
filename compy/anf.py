# ANF: Convert expressions to A-Normal Form

from dataclasses import dataclass, field
from compy.common import CompiledFunction, CompilerState
from compy.syntax import Binding, ConstLiteral, Expression, ImmConstLiteral, Name, NewScope, Node, Scope, ScopeInformation, Statement, VarInfo, mk_exprscope

# List of immediate types for ANF purposes:
IMM = Name | ImmConstLiteral

def anf(comp_state: CompilerState, funcs: list[CompiledFunction]):
    for func in funcs:
        anf_state = ANFState()
        def visit(node: Node) -> Node:
            binds = BindingsBuilder(comp_state, anf_state)
            for field in node.child_fields():
                need_imm = field.need_imm
                def process(cnode: Node) -> Node:
                    cnode = visit(cnode)
                    if need_imm:
                        return imm(binds.process_imm_expr(coerce_expr(cnode)))
                    else:
                        return cnode
                match field.get():
                    case Node() as child:
                        field.set(process(child))
                    case nodes:
                        field.set(map(process, nodes))
            if (bindings := binds.bindings):
                match node:
                    case Expression():
                        return mk_exprscope(node.span, bindings, node, info=ScopeInformation())
                    case Statement():
                        return NewScope(span=node.span, body=Scope(bindings + [node], info=ScopeInformation()))
                    case _: # pragma: no cover
                        assert False, 'Cannot ANF something that is neither an expression or statement'
            return node
        visit(func.body)

def coerce_expr(node: Node) -> Expression:
    assert isinstance(node, Expression)
    return node

@dataclass
class ANFState:
    next_ctr: int = 0

    def get_var_name(self) -> str:
        self.next_ctr += 1
        return f'$anf{self.next_ctr}'

@dataclass
class BindingsBuilder:
    comp_state: CompilerState
    anf_state: ANFState
    bindings: list[Statement] = field(default_factory=list)

    def process_imm_expr(self, expr: Expression) -> IMM:
        match expr:
            case Name(): # Already an immediate
                return expr
            case ConstLiteral():
                return self.comp_state.const_pool.pool(expr)
            case _:
                var_name = self.anf_state.get_var_name()
                info = VarInfo(origin_function_id=-1, mutable=False)
                self.bindings.append(Binding(span=expr.span, mutable=False,
                    name=var_name,
                    init_val=expr,
                    info=info))
                return Name(span=expr.span, name=var_name, info=info)

# Allow type checker to help catch errors
def imm(ex: IMM) -> Expression:
    return ex
