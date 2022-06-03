from dataclasses import dataclass
from enum import Enum
from typing import List, TextIO

from compy.common import MAIN, CompilerInfo


EOL = '\n'

class Operand:
    # To assembly format
    def assemble(self) -> str:
        raise NotImplementedError
    def __str__(self) -> str:
        return self.assemble()

class Reg(Operand, Enum):
    RAX = 'rax'
    RCX = 'rcx'
    RBP = 'rbp'
    RSP = 'rsp'

    def assemble(self) -> str:
        return self.value

@dataclass
class Const(Operand):
    value: int
    def assemble(self) -> str:
        return str(self.value)

class AsmLine:
    def assemble(self) -> str:
        raise NotImplementedError
    def asm_line(self):
        return self.assemble() + EOL
    def __str__(self) -> str:
        return self.assemble()

@dataclass
class Label(AsmLine):
    label: str
    def assemble(self) -> str:
        return self.label + ':'

@dataclass
class Instruction(AsmLine):
    mnemonic: str
    operands: List[Operand]
    def assemble(self) -> str:
        return f'\t{self.mnemonic} {", ".join(operand.assemble() for operand in self.operands)}'

def mov(dst: Operand, src: Operand):
    return Instruction('mov', [dst, src])

PREAMBLE = f"""
section .text
global {MAIN}
"""

MAIN_LABEL = Label(MAIN)

def output(dst: TextIO, lines: List[AsmLine]):
    dst.writelines(line.assemble() for line in lines)

def assemble(info: CompilerInfo, lines: List[AsmLine]):
    with open(info.src_prefix + '.nasm', 'w') as nasm:
        output(nasm, lines)
    # TODO: run nasm on the output
