from dataclasses import dataclass, field

from compy.common import CompileError
from compy.constpool import ConstPool
from compy.strpool import StringPool


@dataclass
class CompilerState:
    errors: list[CompileError] = field(default_factory=list)
    const_pool: ConstPool = field(default_factory=lambda: ConstPool())
    string_pool: StringPool = field(default_factory=lambda: StringPool())
    def err(self, error: 'CompileError'):
        self.errors.append(error)
