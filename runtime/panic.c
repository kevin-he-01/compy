#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include "common.h"
#include "panic.h"

const char* panic_dumpfile; // Used to facilitate testing

static const char *REASON_STRING[] = {
    FOREACH_REASON(REASON_GEN_STRING)
};

static inline const char *str_reason(reason_t reason) {
    return REASON_STRING[reason];
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
    exit(PANIC_EXIT_CODE);
}

// TODO: inline this
void assert_type(location_t location, const char* operation, arg_t arg, type_t required_type) {
    if (arg->type != required_type)
        panic(location, TYPE_ERROR, "%s expected type %s, but %s found",
            operation, to_typename(required_type), to_typename(arg->type));
}
