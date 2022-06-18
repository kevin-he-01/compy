from dataclasses import dataclass
from compy.common import CompilerState, IntegerOOB

from compy.syntax import Integer, Node, NodeWalker


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
            case _:
                return super().walk(node, ctx)
