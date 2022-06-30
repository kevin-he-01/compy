from dataclasses import dataclass, field
import itertools
from typing import Iterable
from compy.asm import AsmLine, Const, Label, db_s

from compy.syntax import StringLiteral


@dataclass
class StringPool:
    symbols: dict[str, str] = field(default_factory=dict)
    str_num: int = 0

    def gen_symbol(self) -> str:
        self.str_num += 1
        return f'_compy_str_{self.str_num}'
    
    def process(self, sl: StringLiteral):
        if sl.content not in self.symbols:
            self.symbols[sl.content] = self.gen_symbol()
        sl.data_label = self.symbols[sl.content]
    
    # Put in in some .rodata section
    def to_asm(self) -> Iterable[AsmLine]:
        for literal, symbol in self.symbols.items():
            yield Label(symbol)
            # For now, null terminate everything as we don't have separate fields for string legth
            yield db_s(itertools.chain((Const(i) for i in literal.encode()), [Const(0)]))
