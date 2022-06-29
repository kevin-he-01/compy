#ifndef COMPY_PANIC_H
#define COMPY_PANIC_H

#include "common.h"

// Same choice as Rust, help distinguish between the common programmatic exit(1)
#define PANIC_EXIT_CODE (101)

typedef long location_t; // for debug information

// Add panic reasons here
#define FOREACH_REASON(FUNC) \
    FUNC(TYPE_ERROR) \
    FUNC(ARITH_OVERFLOW) \
    FUNC(DIV_BY_ZERO) \
    FUNC(EVAL_SYNTAX) \
    FUNC(IO_ERROR) \

#define REASON_GEN_ENUM(ENUM) ENUM,
#define REASON_GEN_STRING(STRING) #STRING,

typedef enum {
    FOREACH_REASON(REASON_GEN_ENUM)
} reason_t; // Panic reasons

extern const char* panic_dumpfile;

void panic(location_t location, reason_t reason, const char *fmt, ...) __attribute__ ((noreturn));
void assert_type(location_t location, const char* operation, arg_t arg, type_t required_type);

#endif /* COMPY_PANIC_H */
