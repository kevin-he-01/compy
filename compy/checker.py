from dataclasses import dataclass
from compy.common import FuncArgsError, IntegerOOB
from compy.state import CompilerState

from compy.syntax import Input, Integer, Node, NodeWalker, RuntimeCall


INT_BITS = 64

# Signed integers
MAX_INT = (1 << (INT_BITS - 1)) - 1
MIN_INT = -(1 << (INT_BITS - 1))

# Unsigned integers
MAX_UINT = (1 << INT_BITS) - 1
MIN_UINT = 0

def check(state: CompilerState, n: Node):
    Checker(state).walk(n, None)

@dataclass
class Checker(NodeWalker[None]):
    state: CompilerState
    def walk(self, node: Node, ctx: None):
        match node:
            case Integer(value=v):
                # For now, assume everything is signed
                if not (MIN_INT <= v <= MAX_INT):
                    self.state.err(IntegerOOB(val=v, span=node.span))
                # Integr is a leaf so no recursive walks
            case Input(args=args):
                if len(args) not in {0, 1}:
                    self.state.err(FuncArgsError(f"input() expects 0 or 1 position arguments but got {len(args)}", span=node.span))
            case RuntimeCall():
                if (err := node.check()) is not None:
                    self.state.err(FuncArgsError(f"{node.func_name()}() {err}", span=node.span))
            case _:
                return super().walk(node, ctx)
