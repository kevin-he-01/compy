from pprint import pprint
from typing import Callable

import compy.asm
import compy.checker
import compy.codegen
import compy.parser
import compy.stack
import compy.tagger
from compy.common import CompileError, CompilerInfo, report_error

DEBUG_HEADER_WIDTH = 50

def run(info: CompilerInfo):
    oprint = info.print
    def debug(step_name: str, action: Callable[[], None]):
        if info.debug_flags.pipeline: # pragma: no cover
            oprint('=' * DEBUG_HEADER_WIDTH)
            oprint(step_name.center(DEBUG_HEADER_WIDTH, '='))
            oprint('=' * DEBUG_HEADER_WIDTH)
            oprint()
            action()
            oprint()
    
    with open(info.src_path) as src:
        code = src.read()
    try:
        top = compy.parser.parse(code, info.src_path)
    except CompileError as ce:
        report_error(info, code, ce)
        raise ce
    compy.checker.check(info.state, top)
    debug('Bare AST', lambda: pprint(top))
    funcs = compy.tagger.tag(info.state, top)
    debug('Tagged AST', lambda: pprint(top))

    # Process diagnostics
    if (errors := info.state.errors):
        for err in errors:
            report_error(info, code, err)
        raise errors[0] # Abort
    # TODO: report warnings but don't terminate

    # All steps starting now SHOULD NOT fail!
    # TODO: run ANF
    compy.stack.allocate_stack(funcs)
    debug('Post stack processing', lambda: pprint(funcs))
    lines = compy.codegen.compile_prog(funcs)
    compy.asm.build(info, lines)
    oprint('Build successful!')
