from dataclasses import dataclass, field
from typing import Iterable
from compy.asm import AsmLine, Const, Label, dq
from compy.common import PrimType

from compy.syntax import ConstLiteral, ImmConstLiteral


CR = tuple[PrimType, int] # Constant record

@dataclass
class ConstPool:
    symbols: dict[CR, str] = field(default_factory=dict)
    const_num: int = 0

    def gen_symbol(self) -> str:
        self.const_num += 1
        return f'_compy_const_{self.const_num}'
    
    def pool(self, literal: ConstLiteral) -> ImmConstLiteral:
        record = (literal.type(), literal.val())
        if record not in self.symbols:
            self.symbols[record] = self.gen_symbol()
        return ImmConstLiteral(span=literal.span, symbol=self.symbols[record])
    
    # Put in in some .rodata section
    def to_asm(self) -> Iterable[AsmLine]:
        for (ty, val), symbol in self.symbols.items():
            yield Label(symbol)
            yield dq(Const(val))
            yield dq(Const(ty.code()))
