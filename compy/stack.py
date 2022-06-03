# Stack allocator

from dataclasses import dataclass


STACK_ALIGNMENT = 16

@dataclass
class Position:
    alloc: 'StackAllocator'
    pos: int = 0

    def allocate(self, num_bytes: int) -> int:
        self.pos -= num_bytes
        self.alloc.require_minimum_space(self.stack_requirement())
        return self.pos
    
    def stack_requirement(self) -> int:
        return -(self.pos - self.pos % STACK_ALIGNMENT)
    
    def fork(self) -> 'Position':
        return Position(self.alloc, self.pos)

class StackAllocator:
    space: int = 0
    def __init__(self) -> None:
        self.root = Position(self) # The root scope position
    
    def require_minimum_space(self, minimum: int):
        self.space = max(self.space, minimum)
