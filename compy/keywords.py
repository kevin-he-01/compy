from compy.common import PrimType
from compy.syntax import UnaryOp


VAL = 'val'
VAR = 'var'
PRINT = 'print'
ADD1 = 'add1'
SUB1 = 'sub1'
UNDERSCORE = '_'
LOOP = 'loop'
TYPE = 'type'

PRIM_TYPE_MAP = {'int': PrimType.INT, 'NoneType': PrimType.NONE, 'type': PrimType.TYPE}

ALL_KEYWORDS = {VAL, VAR, PRINT, ADD1, SUB1, UNDERSCORE, TYPE, *PRIM_TYPE_MAP.keys()}

KW_UNARY_OPS = {PRINT: UnaryOp.PRINT, ADD1: UnaryOp.ADD1, SUB1: UnaryOp.SUB1}

def is_keyword(s: str) -> bool:
    return s in ALL_KEYWORDS

def name_to_type(name: str) -> PrimType:
    return PRIM_TYPE_MAP[name]

def is_type_name(name: str) -> bool:
    return name in PRIM_TYPE_MAP
