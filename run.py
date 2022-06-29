#! /usr/bin/env python3

from subprocess import check_call
from compy import start

check_call('strict-build-runtime')
start()
