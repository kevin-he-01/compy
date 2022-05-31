import argparse
# import sys
from typing import Sequence

import compy.common
import compy.pipeline

SUFFIX = '.compy'

def main(args: Sequence[str] | None = None):
    # print('Argv: ', sys.argv)
    # print('Main: ', args)
    parser = argparse.ArgumentParser(prog=__name__,
                                    description='A compiler')
    parser.add_argument('source', help='The source code to compile')
    # parser.add_argument('-o', '--output', help='The path to the output executable')
    options = parser.parse_args(args)
    source: str = options.source
    if not source.endswith(SUFFIX):
        raise ValueError(f'Source file "{source}" does not end in {SUFFIX}')
    prefix = source[:-len(SUFFIX)]
    info = compy.common.CompilerInfo(source, prefix, prefix + '.out')
    compy.pipeline.run(info)

def start():
    try:
        main()
    except Exception as e:
        print(f'Error: {e}')
