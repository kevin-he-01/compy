#include <time.h>
#include <unistd.h>
#include <limits.h>
#include <stdlib.h>
#include "common.h"
#include "panic.h"
// I/O utilities

obj_t compy_time_int(UNUSED location_t dbg) {
    return INT_VAL(time(NULL));
}

obj_t compy_sleep(location_t dbg, arg_t duration) {
    // TODO: support floating point later on
    assert_type(dbg, "sleep()", duration, TYPE_INT);
    signed long length = duration->val.si_int;
    if (length < 0) {
        panic(dbg, VALUE_ERROR, "sleep(): Sleep length must be non-negative");
    }
    if (length > (signed long) UINT_MAX) {
        panic(dbg, ARITH_OVERFLOW, "sleep(): Sleep length exceeds UINT_MAX");
    }
    if (sleep((unsigned int) length) != 0) { // TODO: restart 
        panic(dbg, IO_ERROR, "sleep(): Interrupted by signal handler");
    }
    return NONE_VAL;
}

obj_t compy_exit(location_t dbg, arg_t exit_code) {
    assert_type(dbg, "exit()", exit_code, TYPE_INT);
    signed long code = exit_code->val.si_int;
    exit((int) code); // truncate to int (eventually actually & 0xff)
    // Never returns
}
