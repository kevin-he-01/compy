from compy.common import CompileError
from tests import common


BOA = 'boa'

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
