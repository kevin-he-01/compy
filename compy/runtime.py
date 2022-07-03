FIXED_ARITY_FUNCS: dict[str, tuple[str, int]] = {
    'time_int': ('compy_time_int', 0),
    'sleep': ('compy_sleep', 1),
    'exit': ('compy_exit', 1),
}

RUNTIME_SYMBOLS = {sym for (sym, _) in FIXED_ARITY_FUNCS.values()}
