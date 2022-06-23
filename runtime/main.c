#include <stdio.h>
#include <stdlib.h>
#include "panic.h"

// External references
extern void compy_main(void);

// Main
int main(void) {
    panic_dumpfile = getenv("COMPY_PANIC_DUMPFILE");
    compy_main();
    return 0;
}
