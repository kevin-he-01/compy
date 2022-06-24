from dataclasses import dataclass
from enum import Enum
import os
import subprocess
import tempfile
from typing import TextIO

from compy.common import CompilerInfo


EOL = '\n'

class Operand:
    # To assembly format
    def assemble(self) -> str:
        raise NotImplementedError

class Reg(Operand, Enum):
    RAX = 'rax'
    RCX = 'rcx'
    RDX = 'rdx'
    RDI = 'rdi'
    RSI = 'rsi'
    R8 = 'r8'
    R9 = 'r9'
    RBP = 'rbp'
    RSP = 'rsp'

    def assemble(self) -> str:
        return self.value

class WordSize(Enum):
    BYTE = 'byte'
    WORD = 'word'
    DWORD = 'dword'
    QWORD = 'qword'

    def notation(self) -> str:
        return self.value

@dataclass
class Const(Operand):
    value: int
    def assemble(self) -> str:
        return str(self.value)

@dataclass(kw_only=True)
class MemOperand(Operand):
    size: WordSize = WordSize.QWORD
    def address(self) -> str:
        raise NotImplementedError
    def assemble(self) -> str:
        return self.size.notation() + ' [' + self.address() + ']'

@dataclass
class Symbol(Operand):
    name: str
    def assemble(self) -> str:
        return self.name

def offset_suffix(offset: int):
    if offset == 0:
        return ''
    elif offset > 0:
        return f' + {offset}'
    else: # offset < 0
        return f' - {-offset}'

@dataclass
class MemRegOffset(MemOperand):
    reg: Reg
    offset: int
    def address(self) -> str:
        return self.reg.assemble() + offset_suffix(self.offset)

class AsmLine:
    def assemble(self) -> str:
        raise NotImplementedError
    def asm_line(self):
        return self.assemble() + EOL

@dataclass
class Label(AsmLine):
    label: str
    def assemble(self) -> str:
        return self.label + ':'

@dataclass
class Instruction(AsmLine):
    mnemonic: str
    operands: list[Operand]
    def assemble(self) -> str:
        return f'\t{self.mnemonic} {", ".join(operand.assemble() for operand in self.operands)}'

@dataclass
class Directive(AsmLine):
    mnemonic: str
    arg: str
    def assemble(self) -> str:
        return f'{self.mnemonic} {self.arg}'

# Directives

def global_(sym: str):
    return Directive('global', sym)

def extern(sym: str):
    return Directive('extern', sym)

# Instructions

def mov(dst: Operand, src: Operand):
    return Instruction('mov', [dst, src])

def add(op1: Operand, op2: Operand):
    return Instruction('add', [op1, op2])

def sub(op1: Operand, op2: Operand):
    return Instruction('sub', [op1, op2])

def neg(op: Operand):
    return Instruction('neg', [op])

def call(op: Operand):
    return Instruction('call', [op])

def push(arg: Operand):
    return Instruction('push', [arg])

def pop(arg: Operand):
    return Instruction('pop', [arg])

def ret():
    return Instruction('ret', [])

# Instructions end

PREAMBLE = "section .text\n"

def output(dst: TextIO, lines: list[AsmLine]):
    dst.writelines(line.asm_line() for line in lines)

RUNTIME_OBJ = 'runtime.o'

def build(info: CompilerInfo, lines: list[AsmLine]):
    oprint = info.print
    def run_cmd(args: list[str]):
        oprint('+ ' + ' '.join(args))
        subprocess.check_call(args)
    with tempfile.TemporaryDirectory() as tmpdir:
        def prefix(debug: bool) -> str:
            return info.src_prefix if debug else (tmpdir + '/compy')
        nasm_file = prefix(info.debug_flags.asm) + '.nasm'
        obj_file = prefix(info.debug_flags.obj) + '.o'
        with open(nasm_file, 'w') as nasm:
            nasm.write(PREAMBLE)
            output(nasm, lines)
        oprint('#### Running build commands...')
        run_cmd(['nasm', '-f', 'elf64', '-o', obj_file, nasm_file])
        run_cmd(['gcc', '-o', info.out_path, obj_file, os.path.dirname(__file__) + '/../runtime/' + RUNTIME_OBJ])
        oprint('#### Build commands ran successfully...')
