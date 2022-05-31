from pprint import pprint
import compy.parser
from compy.common import CompileError, CompilerInfo, report_error


def run(info: CompilerInfo):
    with open(info.src_path) as src:
        code = src.read()
    try:
        stmts = compy.parser.parse(code, info.src_path)
    except CompileError as ce:
        report_error(info, code, ce)
        raise ce
    pprint(stmts)
