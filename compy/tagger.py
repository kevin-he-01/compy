from dataclasses import dataclass, field

from compy.common import (ID, MAIN, CompiledFunction,
                          ImmutableVarError, MutableClosureVarError,
                          SourceSpan, UnboundVarError)
from compy.state import CompilerState
from compy.syntax import (Assignment, Binding, Name, Node, NodeWalker, Scope,
                          ScopeInformation, VarInfo)

MAIN_ID = 1

def tag(state: CompilerState, top: Scope) -> list[CompiledFunction]:
    funcs = tag_functions(state, top)
    tag_variables(state, top)
    return funcs

# First pass, tag scopes with list of functions
def tag_functions(state: CompilerState, top: Scope) -> list[CompiledFunction]:
    FunctionTagger(state).walk(top, None)
    # TODO: extract functions discovered from instance variables
    return [CompiledFunction(symbol=MAIN, body=top, id=MAIN_ID)]

# Second pass
def tag_variables(state: CompilerState, top: Scope):
    VariableTagger(state).walk(top, VariableContext(current_func_id=MAIN_ID))

# Errors to check
# Duplicate function names

@dataclass
class FunctionTagger(NodeWalker[None]):
    state: CompilerState
    def walk(self, node: Node, ctx: None):
        match node:
            case Scope():
                super().walk(node, ctx)
                # TODO: for now, assume no functions
                node.info = ScopeInformation([])
                # Post-order traversal (since functions are declared as children of scopes)
            case _:
                super().walk(node, ctx)

@dataclass
class VariableContext:
    current_func_id: int
    bindings: dict[ID, VarInfo] = field(default_factory=dict)

    def clone(self):
        return VariableContext(current_func_id=self.current_func_id, bindings=dict(self.bindings))

@dataclass
class VariableTagger(NodeWalker[VariableContext]):
    state: CompilerState
    # TODO: keep track of current funct
    def walk(self, node: Node, ctx: VariableContext):
        def reference_name(name: ID, span: SourceSpan) -> VarInfo | None:
            if name not in ctx.bindings:
                self.state.err(UnboundVarError(name, span))
                return None
            info = ctx.bindings[name]
            if ctx.current_func_id != info.origin_function_id and info.mutable:
                self.state.err(MutableClosureVarError(name, span))
            return info
        match node:
            case Scope(info=info):
                assert info != None, 'Untagged scope found'
                assert info.funcs == [] # TODO: add function bindings to ctx as variables
                super().walk(node, ctx.clone())
            case Binding(mutable=mutable, name=name):
                super().walk(node, ctx)
                info = VarInfo(origin_function_id=ctx.current_func_id, mutable=mutable)
                node.info = info
                # TODO: issue shadowing warning here if name in ctx.bindings
                ctx.bindings[name] = info
            case Name(name=name, span=span):
                if (info := reference_name(name, span)):
                    node.info = info
                # Name is a leaf so no need to super().walk
            case Assignment(name=name, target_span=span):
                super().walk(node, ctx)
                if (info := reference_name(name, span)) is None:
                    return
                node.info = info
                if not info.mutable:
                    self.state.err(ImmutableVarError(name, span))
            # TODO: case <function definition>: clone and change ctx.current_func_id
            case _:
                super().walk(node, ctx)
