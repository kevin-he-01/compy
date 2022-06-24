from compy.common import ImmutableVarError, IntegerOOB, UnboundVarError
from tests import common

CHECKER_PREFIX = 'checker'

class TestIntegerBounds(common.CompyTestCase):
    def prefix(self) -> list[str]:
        return [CHECKER_PREFIX, 'int-bounds']
    
    def test_big(self):
        self.compile_failure('big', IntegerOOB)
    
    def test_ok_negative_small(self):
        self.success_case('ok-negative-small', b'-9223372036854775808\n')
    
    def test_ok_negative(self):
        self.success_case('ok-negative', b'-1\n')

    def test_ok(self):
        self.success_case('ok', b'9223372036854775807\n')

    def test_small(self):
        self.compile_failure('small', IntegerOOB)

class TestMisc(common.CompyTestCase):
    def prefix(self) -> list[str]:
        return [CHECKER_PREFIX, 'misc']
    
    def test_scope_e0(self):
        self.compile_failure('scope-e0', UnboundVarError)

    def test_scope_e1(self):
        self.compile_failure('scope-e1', UnboundVarError)

    def test_scope_e2(self):
        self.compile_failure('scope-e2', UnboundVarError)

    def test_ro_e0(self):
        self.compile_failure('ro-e0', ImmutableVarError)

    def test_assign_ub(self):
        self.compile_failure('assign-ub', UnboundVarError)
