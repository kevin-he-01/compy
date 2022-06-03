VAL = 'val'
VAR = 'var'
PRINT = 'print'
ADD1 = 'add1'
SUB1 = 'sub1'
UNDERSCORE = '_'
LOOP = 'loop'

ALL_KEYWORDS = {VAL, VAR, PRINT, ADD1, SUB1, UNDERSCORE}

def is_keyword(s: str) -> bool:
    return s in ALL_KEYWORDS
