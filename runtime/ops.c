#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <limits.h>
#include <stdbool.h>
#include <stdarg.h>
#include <string.h>
#include <errno.h>
#include "common.h"
#include "panic.h"

const obj_t one = INT_VAL(1);

// Support code that passes argument via registers (instead of pointers)
/*
#define REGPASS_PRIM1(name) obj_t name##_(location_t debug_info, obj_t o) { \
                                return name(debug_info, &o); \
                            }
*/

#define ARITH_OP(op_name, op_str) \
obj_t compy_##op_name(location_t debug_info, arg_t x, arg_t y) { \
    assert_type(debug_info, op_str, x, TYPE_INT); \
    assert_type(debug_info, op_str, y, TYPE_INT); \
    long result; \
    bool ovf = __builtin_s##op_name##l_overflow(x->val.si_int, y->val.si_int, &result); \
    if (ovf) { \
        panic(debug_info, ARITH_OVERFLOW, "Overflow on " op_str); \
    } \
    return INT_VAL(result); \
}

// Sample expansion:
// obj_t add(location_t debug_info, arg_t x, arg_t y) {
//     assert_type(debug_info, "+", x, TYPE_INT);
//     assert_type(debug_info, "+", y, TYPE_INT);
//     long result;
//     bool ovf = __builtin_saddl_overflow(x->val.si_int, y->val.si_int, &result);
//     if (ovf) {
//         panic(debug_info, ARITH_OVERFLOW, "Overflow on " "+");
//     }
//     return INT_VAL(result);
// }

#define DIV_MOD_OP(op_name, op_sym) \
obj_t compy_##op_name(location_t debug_info, arg_t left, arg_t right) { \
    assert_type(debug_info, #op_sym, left, TYPE_INT); \
    assert_type(debug_info, #op_sym, right, TYPE_INT); \
    long lv = left->val.si_int, rv = right->val.si_int; \
    if (rv == 0L) { \
        panic(debug_info, DIV_BY_ZERO, "Division by zero"); \
    } \
    if ((lv == LONG_MIN) && (rv == -1L)) { \
        panic(debug_info, ARITH_OVERFLOW, "Overflow on " #op_sym); \
    } \
    return INT_VAL(lv op_sym rv); \
}

static void print_val(arg_t o) {
    // Print value without newlines
    switch (o->type) {
    case TYPE_INT:
        printf("%ld", o->val.si_int);
        break;
    case TYPE_NONE:
        printf("None");
        break;
    case TYPE_TYPE:
        printf("%s", to_typename(o->val.type));
        break;
    case TYPE_BOOL:
        printf(o->val.un_int ? "True" : "False");
        break;
    case TYPE_STRING:
        printf("%s", o->val.str);
        break;
    
    default:
        assertm(0, "print_val: Invalid type code");
    }
}

static obj_t eval(location_t loc, const char *expr) {
    type_t type = from_typename(expr);
    if (type != TYPE_INVALID)
        return TYPE_VAL(type);
    char *endptr;
    if (!strcmp("True", expr)) {
        return BOOL_VAL(1);
    } else if (!strcmp("False", expr)) {
        return BOOL_VAL(0);
    } else if (!strcmp("None", expr)) {
        return NONE_VAL;
    }
    errno = 0;
    long ival = strtol(expr, &endptr, 10);
    if (errno) {
        // TODO: introduce a new syntax error for evaluation
        panic(loc, EVAL_SYNTAX, "Bad integer %s: %s", expr, strerror(errno));
    }
    if (endptr == expr) {
        panic(loc, EVAL_SYNTAX, "Bad expression '%s'", expr);
    }
    if (*endptr != '\0') { // Disallow things like 1j for now
        panic(loc, EVAL_SYNTAX, "Integer with trailing suffix '%s' not allowed: %s", endptr, expr);
    }
    return INT_VAL(ival);
}

/////////////////////
// Runtime exports //
/////////////////////

// Misc

#define SEP " " // TODO: allow customizing this value later on
#define END "\n"

obj_t print_variadic(UNUSED location_t debug_info, int nargs, ...) {
    va_list args;
    va_start(args, nargs);
    for (int i = 0; i < nargs; i++) {
        if (i)
            printf("%s", SEP);
        print_val(va_arg(args, arg_t));
    }
    va_end(args);
    printf("%s", END);
    return NONE_VAL;
}

// Removed
// obj_t print(location_t debug_info, arg_t o) {
//     return print_variadic(debug_info, 1, o);
// }

// Arithmetic

// Caller MUST free the returned line after use (transfer ownership of pointer to caller)
static char *input_line(location_t debug_info, arg_t prompt) {
    if (prompt) { // Not NULL
        print_val(prompt);
        fflush(stdout);
    }
    char *line = NULL;
    size_t len = 0;
    ssize_t nread;

    if ((nread = getline(&line, &len, stdin)) == -1) {
        if (feof(stdin)) {
            panic(debug_info, IO_ERROR, "Reached EOF when reading a line");
        }
        panic(debug_info, IO_ERROR, "Error reading line: %s", strerror(errno));
    }

    // Strip ending newline
    if (nread && line[nread - 1] == '\n') {
        line[nread - 1] = '\0';
    }

    return line;
}

// The Python 2 input()
obj_t eval_input(location_t debug_info, arg_t prompt) {
    char *line = input_line(debug_info, prompt); // TODO: ignore starting and trailing newlines
    obj_t res = eval(debug_info, line);
    free(line);
    return res;
}

obj_t negate(location_t debug_info, arg_t x) {
    assert_type(debug_info, "negate (-)", x, TYPE_INT);
    long value = x->val.si_int;
    if (value == LONG_MIN) {
        panic(debug_info, ARITH_OVERFLOW, "Overflow negating the most negative integer");
    }
    return INT_VAL(-value);
}

ARITH_OP(add, "+")
ARITH_OP(sub, "-")
ARITH_OP(mul, "*")

obj_t add1(location_t debug_info, arg_t x) {
    return compy_add(debug_info, x, &one);
}

obj_t sub1(location_t debug_info, arg_t x) {
    return compy_sub(debug_info, x, &one);
}

DIV_MOD_OP(div, /)
DIV_MOD_OP(mod, %)

// Boolean

unsigned long extract_bool(location_t debug_info, obj_t b) {
    // TODO: accept strings other than "if statement", like "if expression" via an argument
    assert_type(debug_info, "boolean required here", &b, TYPE_BOOL);
    return b.val.un_int;
}

obj_t boolean_not(location_t debug_info, arg_t b) {
    assert_type(debug_info, "not", b, TYPE_BOOL); 
    return BOOL_VAL(!(b->val.un_int));
}

obj_t boolean_and(location_t debug_info, arg_t b1, arg_t b2) {
    assert_type(debug_info, "and", b1, TYPE_BOOL); 
    assert_type(debug_info, "and", b2, TYPE_BOOL); 
    return BOOL_VAL((b1->val.un_int) && (b2->val.un_int));
}

obj_t boolean_or(location_t debug_info, arg_t b1, arg_t b2) {
    assert_type(debug_info, "or", b1, TYPE_BOOL); 
    assert_type(debug_info, "or", b2, TYPE_BOOL); 
    return BOOL_VAL((b1->val.un_int) || (b2->val.un_int));
}

// Comparison

obj_t is_identical(UNUSED location_t debug_info, arg_t a, arg_t b) {
    // Reinterpret everything as `unsigned long` to compare underlying representation
    return BOOL_VAL((a->type == b->type) && (a->val.un_int == b->val.un_int));
}

obj_t is_eq(location_t debug_info, arg_t a, arg_t b) {
    // TODO: For now, assume everything is equal IFF the representation is equal
    // Representation must be canonicalized (None MUST have 0 as value field)
    // Will not be the case for floating point (0.0 and -0.0)
    return is_identical(debug_info, a, b);
}

#define CMP_OP(func_name, operator) \
obj_t func_name(location_t debug_info, arg_t a, arg_t b) { \
    assert_type(debug_info, #operator, a, TYPE_INT);  \
    assert_type(debug_info, #operator, b, TYPE_INT); \
    return BOOL_VAL(a->val.si_int operator b->val.si_int); \
}

// Sample:
// obj_t is_le(location_t debug_info, arg_t a, arg_t b) {
//     assert_type(debug_info, "<", a, TYPE_INT); 
//     assert_type(debug_info, "<", b, TYPE_INT);
//     return BOOL_VAL(a->val.si_int < b->val.si_int);
// }

CMP_OP(is_lt, <)
CMP_OP(is_gt, >)
CMP_OP(is_le, <=)
CMP_OP(is_ge, >=)
