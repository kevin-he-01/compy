from tests import common

STRING_PREFIX = 'string'

class TestStringLiterals(common.CompyTestCase):
    def prefix(self) -> list[str]:
        return [STRING_PREFIX, 'literal']

    def test_dup(self):
        self.success_case('dup', stdout=b'bazaar cathedral bazaar\n')
    
    def test_hello_world(self):
        self.success_case('hello-world', stdout=b'Hello, world!\n')
    
    def test_prompt(self):
        self.success_case('prompt',
            stdout=b'What is your favorite number? -1024 is a cool number.\n',
            stdin=b'-1024')
    
    def test_unicode(self):
        self.success_case('unicode', 'I ❤️ compy!\n'.encode())

    def test_eq(self):
        self.success_case('eq', EQ_OUTPUT)

EQ_OUTPUT = b'''True
False
False
True
False
True
'''
