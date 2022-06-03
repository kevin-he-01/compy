from pprint import pprint
import compy.parser
import compy.tagger
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
    compy.tagger.tag(info.state, top)
    print('***DEBUG TAGGED AST***')
    pprint(top)

    if (errors := info.state.errors):
        for err in errors:
            report_error(info, code, err)
        raise errors[0] # Abort
    # TODO: report warnings but don't terminate

    # The following steps SHOULD NOT fail!
    # TODO: run ANF
    # TODO: run stack allocation
    # TODO: compile
