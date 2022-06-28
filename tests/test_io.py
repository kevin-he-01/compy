from tests import common

IO_PREFIX = 'io'

class TestIO(common.CompyTestCase):
    def prefix(self) -> list[str]:
        return [IO_PREFIX]

    def test_print(self):
        self.success_case('print', b'1 None type int\nbool type NoneType 5\n-100 1 -9223372036854775808\n')

    def test_print_anf(self):
        self.success_case('print-anf', b'5274 9 -25 4\n')

    def test_print_nargs(self):
        self.success_case('print-nargs', TEST_IO_OUT)

TEST_IO_OUT = b'''
1
2 3
4 5 6
7 8 9 10
None 11 None 12 None
14 15 16 17 18 19
14 15 16 17 18 19 20
14 15 16 17 18 19 20 21
'''
