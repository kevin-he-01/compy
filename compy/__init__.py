import argparse
import os
import sys
from typing import Sequence, TextIO

import compy.common
import compy.pipeline

SUFFIX = '.compy'

def main(args: Sequence[str] | None = None, stdout: TextIO = sys.stdout, stderr: TextIO = sys.stderr):
    # print('Argv: ', sys.argv)
    # print('Main: ', args)
    parser = argparse.ArgumentParser(prog=__name__,
                                    description='A compiler')
    parser.add_argument('source', help='The source code to compile')
    parser.add_argument('--debug-pipeline', action='store_true')
    parser.add_argument('--debug-asm', action='store_true')
    parser.add_argument('--debug-obj', action='store_true')
    parser.add_argument('-r', '--run', action='store_true', help='If present, also runs the compiled executable (with no arguments) after compilation. ' +
                                                                 'Do not use this option if calling main() from another program since it uses exec()')
    parser.add_argument('-o', '--output', help='The path to the output executable')
    options = parser.parse_args(args)
    source: str = options.source
    # debug flags
    d_pipeline: bool = options.debug_pipeline
    d_asm: bool = options.debug_asm
    d_obj: bool = options.debug_obj
    run: bool = options.run
    out_path: str | None = options.output

    if not source.endswith(SUFFIX): # pragma: no cover
        raise compy.common.UserError(f'Source file "{source}" does not end in {SUFFIX}')
    prefix = source[:-len(SUFFIX)]
    if out_path == None: # pragma: no cover
        out_path = prefix + '.out'
    flags = compy.common.DebugFlags(d_pipeline, d_asm, d_obj)
    info = compy.common.CompilerInfo(source, prefix, out_path, flags, stdout, stderr)
    compy.pipeline.run(info)
    if run: # pragma: no cover
        print('=====Running executable=====')
        os.execl(info.out_path, info.out_path)

def start(): # pragma: no cover
    try:
        main()
    except (compy.common.UserError, OSError) as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
