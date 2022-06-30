from dataclasses import dataclass
from compy.state import CompilerState
from compy.syntax import Node, NodeWalker, Scope, StringLiteral


def process_str(state: CompilerState, top: Scope):
    StringTagger(state).walk(top, None)

@dataclass
class StringTagger(NodeWalker[None]):
    state: CompilerState
    def walk(self, node: Node, ctx: None):
        match node:
            case StringLiteral():
                self.state.string_pool.process(node)
            case _:
                pass
        super().walk(node, None)
