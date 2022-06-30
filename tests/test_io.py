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

    def test_input0(self):
        self.success_case('input0', b'42\n', stdin=b'42\n')
        self.success_case('input0', b'42\n', stdin=b'42')
        self.success_case('input0', b'-123\n', stdin=b'-123')
        # self.success_case('input0', b'None\n', stdin=b'None')
        # self.success_case('input0', b'bool\n', stdin=b'bool')
        # self.success_case('input0', b'type\n', stdin=b'type')
        # self.success_case('input0', b'False\n', stdin=b'False')
        # self.success_case('input0', b'True\n', stdin=b'True')

    def test_input1(self):
        self.success_case('input1', stdout=b'type\nbool\n9999\n100\nTrue\nNoneType\n', stdin=b'type\nbool\n-1\nTrue\nint\nNone')
        self.success_case('input1', stdout=b'9223372036854775807\n-9223372036854775808\n0\n-42\nFalse\nbool\n',
            stdin=b'9223372036854775807\n-9223372036854775808\n-10000\nFalse\nbool\nFalse')

    def test_input_prompt0(self):
        self.success_case('input-prompt0', b'None1337\n', stdin=b'1337\n')

    def test_input_prompt1(self):
        self.success_case('input-prompt1', b'inttype\n', stdin=b'type')
    
    def test_input_prompt2(self):
        self.success_case('input-prompt2', b'2101\n', stdin=b'100\n')
    
    def test_input_negative(self):
        self.runtime_failure('input0', common.PanicReason.IO_ERROR, stdin=b'') # EOF
        self.runtime_failure('input0', common.PanicReason.EVAL_SYNTAX, stdin=b'\n')
        self.runtime_failure('input0', common.PanicReason.EVAL_SYNTAX, stdin=b'bad')
        self.runtime_failure('input0', common.PanicReason.EVAL_SYNTAX, stdin=b'102z')
    

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
