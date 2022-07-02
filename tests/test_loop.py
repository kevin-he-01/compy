from tests import common

LOOP_PREFIX = 'loops'

class TestWhile(common.CompyTestCase):
    def prefix(self) -> list[str]:
        return [LOOP_PREFIX, 'while']
    
    def test_while0(self):
        self.success_case('while0', b'0\n1\n2\n3\n4\n5\n6\n')

    def test_fibo(self):
        self.success_case('fibo', stdout=FIBO_OUTPUT, stdin=b'100')
    
    def test_gcd(self):
        self.success_case('gcd', stdout=b'a: b: gcd(a,b) = 169\n', stdin=b'2873\n3211\n')

    def test_truth_table(self):
        self.success_case('truth-table', TRUTH_TABLE_OUTPUT)

FIBO_OUTPUT = b'''0
1
1
2
3
5
8
13
21
34
55
89
'''

TRUTH_TABLE_OUTPUT = b'''a b c False False False a&b&c False a|b|c False
a b c False False True a&b&c False a|b|c True
a b c False True False a&b&c False a|b|c True
a b c False True True a&b&c False a|b|c True
a b c True False False a&b&c False a|b|c True
a b c True False True a&b&c False a|b|c True
a b c True True False a&b&c False a|b|c True
a b c True True True a&b&c True a|b|c True
'''
