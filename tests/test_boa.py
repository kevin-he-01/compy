from compy.common import CompileError
from tests import common


BOA = 'boa'

class TestBoa(common.CompyTestCase):
    def prefix(self) -> list[str]:
        return [BOA]

    def test_plus0(self):
        self.success_case('plus0', b'2\n')
    
    def test_plus1(self):
        self.success_case('plus1', b'1110\n')

    def test_plus_e_ovf(self):
        for i in range(1, 5+1):
            self.runtime_failure(f'plus-e-ovf{i}', common.PanicReason.ARITH_OVERFLOW)
    
    def test_mult_e_ovf(self):
        for i in range(1, 3+1):
            self.runtime_failure(f'mult-e-ovf{i}', common.PanicReason.ARITH_OVERFLOW)

    def test_arith(self):
        self.success_case('arith', b'889\n-98\n8\n10\n221\n-30\n-30\n39\n84\n10000\n')

    def test_stress0(self):
        self.success_case('stress0', b'7006652\n')

    def test_div0(self):
        self.success_case('div0', b'256\n255\n-3\n-3\n-2\n2\n0\n')

    def test_div_e_ovf(self):
        self.runtime_failure('div-e-ovf', common.PanicReason.ARITH_OVERFLOW)

    def test_div_e_zero(self):
        self.runtime_failure('div-e-zero', common.PanicReason.DIV_BY_ZERO)

    def test_mod0(self):
        self.success_case('mod0', b'68392\n')

class TestBoaBool(common.CompyTestCase):
    def prefix(self) -> list[str]:
        return [BOA, 'bool']
    
    def test_bool(self):
        self.success_case('bool', b'True\nFalse\n')

    def test_bool_neg(self):
        self.success_case('bool-neg', b'False\nTrue\n')
    
    def test_bool_logical(self):
        self.success_case('bool-logical0', LOGICAL0_OUTPUT)

    def test_bool_short_circuit(self):
        self.success_case('bool-short-circuit', SHORT_CIRCUIT_OUTPUT)

    def test_comparison(self):
        self.success_case('comparison', OUTPUT_COMPARISON)

    def test_if0(self):
        self.success_case('if0', b'1\n10\n')

    def test_if1(self):
        self.success_case('if1', b'1\n20\n31\n30\n')

class TestLet(common.CompyTestCase):
    def prefix(self) -> list[str]:
        return [BOA, 'let']

    def test_shadow(self):
        self.success_case('shadow', b'-2\n')
    
    def test_e0(self):
        self.compile_failure('e0', CompileError)

    def test_empty(self):
        self.success_case('empty', b'NoneType\n')
    
    def test_nested(self):
        self.success_case('nested', b'9\nNone\n10\n7\n')

LOGICAL0_OUTPUT = b'''False
True
True
True
False
False
False
True
'''

SHORT_CIRCUIT_OUTPUT = b'''0
1
False
0
1
True
0
True
0
True
0
False
0
False
0
1
False
0
1
True
'''

OUTPUT_COMPARISON = b'''None
False
True
False
True
False
True
None
True
False
False
12
True
True
False
False
False
22
False
True
True
True
False
32
False
False
False
True
True
'''