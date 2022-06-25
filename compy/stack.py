from dataclasses import dataclass
from compy.asm import MemRegOffset, Reg, WordSize
from compy.common import CompiledFunction

from compy.syntax import Binding, Node, NodeWalker, Scope


# x86-64 System V ABI requires 16-byte alignment of the stack
STACK_ALIGNMENT = 16

@dataclass
class StackPosition:
    alloc: 'StackAllocator'
    pos: int = 0

    def allocate(self, num_bytes: int) -> int:
        self.pos -= num_bytes
        self.alloc.require_minimum_space(self.stack_requirement())
        return self.pos
    
    def stack_requirement(self) -> int:
        return -(self.pos - self.pos % STACK_ALIGNMENT)
    
    # Shallow copy with same allocator but separate position
    def fork(self) -> 'StackPosition':
        return StackPosition(self.alloc, self.pos)

class StackAllocator:
    space: int = 0
    def __init__(self) -> None:
        self.root = StackPosition(self) # The root scope position
    
    def require_minimum_space(self, minimum: int):
        self.space = max(self.space, minimum)

SIZE_UNTYPED = 16

class AllocationWalker(NodeWalker[StackPosition]):
    def walk(self, node: Node, ctx: StackPosition):
        match node:
            case Scope(info=info):
                assert info != None, 'Untagged scope'
                assert info.funcs == [], 'TBD: support function closure as variable names'
                # TODO: allocate space for function closure names as well
                super().walk(node, ctx.fork())
            case Binding(info=info):
                assert info != None, 'Untagged binding'
                super().walk(node, ctx)
                # For now, assume everything is untyped
                info.stack_offset = ctx.allocate(SIZE_UNTYPED)
            # TODO: avoid descending down a function declaration (keep everything under one function)
            case _:
                super().walk(node, ctx)

def allocate_stack(funcs: list[CompiledFunction]):
    for func in funcs:
        alloc = StackAllocator()
        AllocationWalker().walk(func.body, alloc.root)
        func.stack_usage = alloc.space

# Return a memory operand that can be used to access the stack variable at `stack_pos` at offset `offset`
def op_stack(stack_pos: int, offset: int = 0, *, size: WordSize = WordSize.QWORD):
    return MemRegOffset(Reg.RBP, stack_pos + offset, size=size)
