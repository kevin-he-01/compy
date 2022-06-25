#include <stdio.h>
#include <stdint.h>
#include <limits.h>
#include <stdbool.h>
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
obj_t op_name(location_t debug_info, arg_t x, arg_t y) { \
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
obj_t op_name(location_t debug_info, arg_t left, arg_t right) { \
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
} \

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
    
    default:
        assertm(0, "print_val: Invalid type code");
    }
}

// Runtime exports
obj_t print(UNUSED location_t debug_info, arg_t o) {
    print_val(o);
    putchar('\n');
    return NONE_VAL;
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
    return add(debug_info, x, &one);
}

obj_t sub1(location_t debug_info, arg_t x) {
    return sub(debug_info, x, &one);
}

DIV_MOD_OP(div, /)
DIV_MOD_OP(mod, %)
