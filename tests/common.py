from dataclasses import dataclass
from enum import Enum, auto
import io
import os
import subprocess
from typing import Any, Type
import unittest, compy
from compy.common import CompileError

PATH_SPEC = str | list[str]

EXIT_SUCCESS = 0
TESTCASE_DIR = './testcases/'
TEMP_OUTPUT = './testexe.out'
DUMPFILE = '.compy_panic'
DUMP_ENV = 'COMPY_PANIC_DUMPFILE'

class AutoName(Enum):
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]) -> Any:
        return name

class PanicReason(AutoName):
    TYPE_ERROR = auto()
    ARITH_OVERFLOW = auto()
    DIV_BY_ZERO = auto()
    EVAL_SYNTAX = auto()
    IO_ERROR = auto()

    def get_str(self) -> str:
        return self.value

class CompyTestCase(unittest.TestCase):
    # Can override to change the prefix path to test cases
    def prefix(self) -> list[str]:
        return []
    
    def assertOutput(self, args: list[str], expected_stdout: bytes,
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
            case RuntimeFailure(reason=reason):
                run_compiler()
                try:
                    os.remove(DUMPFILE)
                except FileNotFoundError:
                    pass
                os.environ[DUMP_ENV] = DUMPFILE
                try:
                    subprocess.run([TEMP_OUTPUT], input=prog.stdin, capture_output=True)
                finally:
                    del os.environ[DUMP_ENV]
                try:
                    with open(DUMPFILE) as df:
                        self.assertEqual(reason.get_str(), df.read().strip(), 'Wrong panic reason')
                except FileNotFoundError:
                    # Can happen due to SIGSEGV/abnormal termination as well
                    self.fail('Expected program to panic but no panics observed')

    def get_full_path(self, short: PATH_SPEC) -> list[str]:
        match short:
            case str(s):
                return self.prefix() + [s]
            case _: # list
                return self.prefix() + short
    
    # BEGIN TESTCASE HELPERS (similar to builder pattern, high levels ways to construct and run tests)
    def success_case(self, prog_path: PATH_SPEC, stdout: bytes, *,
            stderr: bytes = b'', stdin: bytes = b'', retcode: int = EXIT_SUCCESS):
        self.program_test(ProgramTestCase(self.get_full_path(prog_path),
            Success(output=stdout, stderr=stderr, return_code=retcode), stdin=stdin))

    def compile_failure(self, prog_path: PATH_SPEC, exc: Type[CompileError]):
        self.program_test(ProgramTestCase(self.get_full_path(prog_path),
            CompilerFailure(exc=exc), stdin=b''))

    def runtime_failure(self, prog_path: PATH_SPEC, reason: PanicReason, *, stdin: bytes = b''):
        self.program_test(ProgramTestCase(self.get_full_path(prog_path),
            RuntimeFailure(reason=reason), stdin=stdin))

@dataclass
class Success:
    output: bytes
    stderr: bytes
    return_code: int # Not necessarily EXIT_SUCCESS since non-panicking run may do exit(1)

@dataclass
class CompilerFailure:
    exc: Type[BaseException]

@dataclass
class RuntimeFailure:
    reason: PanicReason

OUTCOME = Success | CompilerFailure | RuntimeFailure

@dataclass
class ProgramTestCase:
    src_path: list[str]
    expected_outcome: OUTCOME
    stdin: bytes
