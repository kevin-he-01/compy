#ifndef COMPY_PANIC_H
#define COMPY_PANIC_H

#include "common.h"

// Same choice as Rust, help distinguish between the common programmatic exit(1)
#define PANIC_EXIT_CODE (101)

typedef long location_t; // for debug information

typedef enum {
    TYPE_ERROR,
    ARITH_OVERFLOW
} reason_t; // Panic reasons

extern const char* panic_dumpfile;

void panic(location_t location, reason_t reason, const char *fmt, ...) __attribute__ ((noreturn));
void assert_type(location_t location, const char* operation, arg_t arg, type_t required_type);

#endif /* COMPY_PANIC_H */
