#ifndef COMPY_COMMON_H
#define COMPY_COMMON_H

#include <assert.h>

// Macros
#define assertm(exp, msg) assert(((void)msg, exp)) // assert with message
#define UNUSED __attribute__((unused))

// Types
typedef unsigned long type_t;

typedef union {
    signed long si_int; // signed int
    unsigned long un_int; // unsigned int
    double flt; // floating point
    type_t type;
} value_t;

typedef struct {
    value_t val;
    type_t type;
} obj_t;

typedef const obj_t* arg_t;

////// Valid compy types //////////
#define TYPE_INT (0UL) // Signed integer
#define TYPE_NONE (1UL)
#define TYPE_TYPE (2UL)
#define TYPE_BOOL (3UL) 
////// Valid compy types end //////

////// Valid compy values //////////
#define NONE_VAL ((obj_t) {.val = {.un_int = 0UL}, .type = TYPE_NONE})
#define INT_VAL(v) ((obj_t) {.val = {.si_int = (v)}, .type = TYPE_INT})
#define BOOL_VAL(v) ((obj_t) {.val = {.un_int = (v)}, .type = TYPE_BOOL})

// Declarations
const char *to_typename(type_t type);

#endif /* COMPY_COMMON_H */
