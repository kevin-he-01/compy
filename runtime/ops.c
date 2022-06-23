#include <stdio.h>
#include <stdint.h>
#include <limits.h>
#include "common.h"
#include "panic.h"

// Support code that passes argument via registers (instead of pointers)
#define REGPASS_PRIM1(name) obj_t name##_(location_t debug_info, obj_t o) { \
                                return name(debug_info, &o); \
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

obj_t add1(location_t debug_info, arg_t x) {
    assert_type(debug_info, "add1()", x, TYPE_INT);
    long value = x->val.si_int;
    if (value == LONG_MAX) {
        panic(debug_info, ARITH_OVERFLOW, "Overflow on add1");
    }
    return INT_VAL(value + 1);
}

obj_t sub1(location_t debug_info, arg_t x) {
    assert_type(debug_info, "sub1()", x, TYPE_INT);
    long value = x->val.si_int;
    if (value == LONG_MIN) {
        panic(debug_info, ARITH_OVERFLOW, "Overflow on sub1");
    }
    return INT_VAL(value - 1);
}

REGPASS_PRIM1(print)
REGPASS_PRIM1(negate)
REGPASS_PRIM1(add1)
REGPASS_PRIM1(sub1)
