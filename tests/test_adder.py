from typing import List
from tests import common


class TestAdder(common.CompyTestCase):
    def prefix(self) -> List[str]:
        return ['adder']
    
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

    def test_expr(self):
        self.success_case('expr', b'5\n')

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
