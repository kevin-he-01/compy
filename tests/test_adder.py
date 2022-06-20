from typing import List
from tests import common


ADDER = 'adder'

class TestAdder(common.CompyTestCase):
    def prefix(self) -> List[str]:
        return [ADDER]
    
    def test_print0(self):
        self.success_case('print0', b'42\n')

    def test_print1(self):
        self.success_case('print1', b'2\n')
    
    def test_stress0(self):
        self.success_case('stress0', STRESS_OUTPUT)
    
    def test_vars0(self):
        self.success_case('vars0', b'-1024\n')

    def test_vars1(self):
        self.success_case('vars1', VARS1_OUTPUT)
    
    def test_vars2(self):
        self.success_case('vars2', VARS2_OUTPUT)

    def test_vars3(self):
        self.success_case('vars3', VARS3_OUTPUT)

    def test_expr(self):
        self.success_case('expr', b'5\n')

class TestTypedAdder(common.CompyTestCase):
    def prefix(self) -> List[str]:
        return [ADDER, 'typed']
    
    def test_print_none(self):
        self.success_case('print-none', b'None\n')

    def test_print_ret(self):
        self.success_case('print-ret', b'-42\nNone\n')

    def test_vars0(self):
        self.success_case('vars0', b'None\n1024\nNone\n')
    
    def test_sub1_negative(self):
        self.runtime_failure('sub1-e-ty', common.PanicReason.TYPE_ERROR)
        self.runtime_failure('sub1-e', common.PanicReason.ARITH_OVERFLOW)
    
    def test_add1_negative(self):
        self.runtime_failure('add1-e-ty', common.PanicReason.TYPE_ERROR)
        self.runtime_failure('add1-e', common.PanicReason.ARITH_OVERFLOW)

    def test_neg_negative(self):
        self.runtime_failure('neg-e0', common.PanicReason.TYPE_ERROR)
        self.runtime_failure('neg-e1', common.PanicReason.ARITH_OVERFLOW)

STRESS_OUTPUT = b'''-123
123
6
7
6
-6
5
-7
-5
133742
6
6
6
-42
'''

VARS1_OUTPUT = b'''0
4
-4
3
1
11
12
-12
'''

VARS2_OUTPUT = b'''1
2
1024
-42
4
-42
4
9
-100
9
-100
-1000
318
323
'''

VARS3_OUTPUT = b'''124
124
457
790
-124
-457
-790
-788
-127
124
122
123
456
789
-123
-456
-789
-787
-125
'''