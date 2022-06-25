from pprint import pprint

from compy.common import SourceSpan
from compy.syntax import *

ss = SourceSpan(1, None, 1, None)
ss2 = SourceSpan(2, None, 2, None)
ss3 = SourceSpan(3, None, 3, None)

def debug_children(n: Node):
    print(f'======CLASS {type(n)}======')
    pprint(n)
    print(f'======CHILDREN======')
    pprint(list(n.children()))
    print(f'======END======')

# e = EvalExpr(ss, Name(ss, 'x'))
# debug_children(e)
# print(list(e.child_fields())[0].get())
# list(e.child_fields())[0].set(Unit(ss))
# # list(e.child_fields())[0].set(NoOp(ss))
# print(list(e.child_fields())[0].get())
# debug_children(e)


# debug_children(Binding(ss, False, 'x', Name(ss, 'y')))
# debug_children(Scope([NoOp(ss), EvalExpr(ss3, Unit(ss3)), NoOp(ss2)]))
e = Scope([NoOp(ss), NoOp(ss2)])
debug_children(e)
list(e.child_fields())[0].set([NoOp(ss3)])
debug_children(e)
# debug_children(Prim1(ss2, UnaryOp.NEGATE, Unit(ss)))
