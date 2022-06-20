#include <stdio.h>
#include <stdint.h>
#include <inttypes.h>
#include <stdlib.h>
#include <assert.h>
#include <stdarg.h>
#include <limits.h>

// Macros
#define assertm(exp, msg) assert(((void)msg, exp)) // assert with message
#define UNUSED __attribute__((unused))

// External references
extern void compy_main(void);

// Types
typedef unsigned long type_t;
typedef long location_t; // for debug information

typedef union {
    long si_int; // signed int
    unsigned long un_int; // unsigned int
    double flt; // floating point
    type_t type;
} value_t;

typedef struct {
    value_t val;
    type_t type;
} obj_t;

typedef const obj_t* arg_t;

typedef enum {
    TYPE_ERROR,
    ARITH_OVERFLOW
} reason_t; // Panic reasons

////// Valid compy types //////////
#define TYPE_INT (0UL) // Signed integer
#define TYPE_NONE (1UL)
#define TYPE_TYPE (2UL)
////// Valid compy types end //////

////// Valid compy values //////////
#define NONE_VAL ((obj_t) {.val = {.un_int = 0UL}, .type = TYPE_NONE})
#define INT_VAL(v) ((obj_t) {.val = {.si_int = (v)}, .type = TYPE_INT})

// Global variables
const char* panic_dumpfile; // Used to facilitate testing

// Runtime exports

const char *str_reason(reason_t reason) {
    switch (reason) {
    case TYPE_ERROR:
        return "TYPE_ERROR";
    
    case ARITH_OVERFLOW:
        return "ARITH_OVERFLOW";
    }
    assertm(0, "Nonexhaustive enum match");
    return "";
}

void dump_panic_reason(const char* reason) {
    if (panic_dumpfile) {
        fprintf(stderr, "Dumping panic reason to file '%s'...\n", panic_dumpfile);
        FILE *df = fopen(panic_dumpfile, "w");
        if (!df) {
            perror("Failed to open dump file");
            return;
        }
        fprintf(df, "%s\n", reason);
        fclose(df);
    }
}

void panic(location_t location, reason_t reason, const char *fmt, ...) {
    const char* reason_str = str_reason(reason);
    fprintf(stderr, "[!] Panic (%s) at line %ld: ", reason_str, location);
    va_list args;
    va_start(args, fmt);
    vfprintf(stderr, fmt, args);
    va_end(args);
    putchar('\n');
    dump_panic_reason(reason_str);
    exit(1);
}

const char *to_typename(type_t type) {
    switch (type) {
    case TYPE_INT:
        return "int";
    case TYPE_NONE:
        return "NoneType";
    case TYPE_TYPE:
        return "type";
    
    default:
        assertm(0, "to_typename: Invalid type code");
        return ""; // Prevent UB when assertions are disabled
    }
}

// TODO: inline this
void assert_type(location_t location, const char* operation, arg_t arg, type_t required_type) {
    if (arg->type != required_type)
        panic(location, TYPE_ERROR, "%s expected type %s, but %s found",
            operation, to_typename(required_type), to_typename(arg->type));
}

void print_val(arg_t o) {
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

// Support code that passes argument via registers (instead of pointers)
#define REGPASS_PRIM1(name) obj_t name##_(location_t debug_info, obj_t o) { \
                                return name(debug_info, &o); \
                            }

REGPASS_PRIM1(print)
REGPASS_PRIM1(negate)
REGPASS_PRIM1(add1)
REGPASS_PRIM1(sub1)

// Main
int main(void) {
    panic_dumpfile = getenv("COMPY_PANIC_DUMPFILE");
    compy_main();
    return 0;
}
