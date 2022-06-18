from dataclasses import dataclass
import io
import subprocess
from typing import List, Type
import unittest, compy
from compy.common import CompileError

EXIT_SUCCESS = 0

TESTCASE_DIR = './testcases/'

TEMP_OUTPUT = './testexe.out'

PATH_SPEC = str | List[str]

class CompyTestCase(unittest.TestCase):
    # Can override to change the prefix path to test cases
    def prefix(self) -> List[str]:
        return []
    
    def assertOutput(self, args: List[str], expected_stdout: bytes,
                    expected_stderr: bytes = b'', expected_exit: int = EXIT_SUCCESS,
                    stdin: bytes = b''):
        progname = args[0]
        proc = subprocess.run(args, input=stdin, capture_output=True)
        if proc.returncode != expected_exit:
            self.fail(f'{progname}: expect exit code {expected_exit}, but got {proc.returncode}')
        # self.assertEqual(expected_stdout, proc.stdout)
        if expected_stdout != proc.stdout:
            self.fail(f'{progname}: expected output: {expected_stdout}, but got: {proc.stdout}')
        if expected_stderr != proc.stderr:
            self.fail(f'{progname}: expected stderr: {expected_stderr}, but got: {proc.stderr}')
        # TODO: allow outputing better error message by writing both into a file and allow the use of `code diff`
    
    # Sample sanity test:
    # def test_sanity(self):
    #     self.assertOutput(['cat'], b'ab', stdin=b'ab')

    # Low level test case methods
    def program_test(self, prog: 'ProgramTestCase'):
        src_path = prog.src_path
        assert src_path, 'src_path cannot be an empty list!'
        prog_path = TESTCASE_DIR + '/'.join(src_path) + compy.SUFFIX
        def run_compiler():
            compy.main(args=[prog_path, '-o', TEMP_OUTPUT], stdout=io.StringIO(), stderr=io.StringIO())
        match prog.expected_outcome:
            case Success(output=stdout, stderr=stderr, return_code=retcode):
                run_compiler()
                self.assertOutput([TEMP_OUTPUT], stdout, expected_stderr=stderr, expected_exit=retcode, stdin=prog.stdin)
            case CompilerFailure(exc=exc):
                with self.assertRaises(exc):
                    run_compiler()

    def get_full_path(self, short: PATH_SPEC) -> List[str]:
        match short:
            case str(s):
                return self.prefix() + [s]
            case _: # List
                return self.prefix() + short
    
    # BEGIN TESTCASE HELPERS (similar to builder pattern, high levels ways to construct and run tests)
    def success_case(self, prog_path: PATH_SPEC, stdout: bytes, *,
            stderr: bytes = b'', stdin: bytes = b'', retcode: int = EXIT_SUCCESS):
        self.program_test(ProgramTestCase(self.get_full_path(prog_path),
            Success(output=stdout, stderr=stderr, return_code=retcode), stdin=stdin))

    def compile_failure(self, prog_path: PATH_SPEC, exc: Type[CompileError]):
        self.program_test(ProgramTestCase(self.get_full_path(prog_path),
            CompilerFailure(exc=exc), stdin=b''))

@dataclass
class Success:
    output: bytes
    stderr: bytes
    return_code: int # Not necessarily EXIT_SUCCESS since non-panicking run may do exit(1)

@dataclass
class CompilerFailure:
    exc: Type[BaseException]

# TBD: implement this when implementing panic (probably output exact reason for panic in a separate file when in debug mode)
# @dataclass
# class RuntimeFailure:
#     pass

OUTCOME = Success | CompilerFailure

@dataclass
class ProgramTestCase:
    src_path: List[str]
    expected_outcome: OUTCOME
    stdin: bytes
