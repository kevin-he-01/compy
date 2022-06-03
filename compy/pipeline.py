from pprint import pprint
import compy.parser
import compy.tagger
import compy.stack
from compy.common import CompileError, CompilerInfo, report_error


def run(info: CompilerInfo):
    with open(info.src_path) as src:
        code = src.read()
    try:
        top = compy.parser.parse(code, info.src_path)
    except CompileError as ce:
        report_error(info, code, ce)
        raise ce
    # TODO: run checker (Ex. number too large)
    print('***DEBUG BARE AST***')
    pprint(top)
    funcs = compy.tagger.tag(info.state, top)
    print('***DEBUG TAGGED AST***')
    pprint(top)

    # Process diagnostics
    if (errors := info.state.errors):
        for err in errors:
            report_error(info, code, err)
        raise errors[0] # Abort
    # TODO: report warnings but don't terminate

    # All steps starting now SHOULD NOT fail!
    # TODO: run ANF
    compy.stack.allocate_stack(funcs)
    print('***DEBUG POST STACK PROCESSING***')
    pprint(funcs)
    # TODO: compile
    # TODO: assemble & link
