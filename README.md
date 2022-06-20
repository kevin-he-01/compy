# Compy

An x86-64 compiler for a Python-like language (source file ends with `*.compy`) written itself in Python.
Most of the parsing work is delegated to [Python's AST module](https://docs.python.org/3/library/ast.html).

Currently supports Python 3.10 only. It uses features (Ex. pattern matching) that are new in 3.10.
In addition, since the Python AST is not guaranteed to stay the same across different Python releases, do not expect the compiler to work out of the box for 3.11 and beyond. (However, since it converts the Python
AST into its own [internal AST](compy/syntax.py), it may be possible to modify [parser.py](compy/parser.py))

Still in the very early stage of development and cannot compile useful programs yet. There are many to-dos.
