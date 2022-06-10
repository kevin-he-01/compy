#include <stdio.h>
#include <stdint.h>
#include <inttypes.h>

extern void compy_main(void);

void print_signed_int(int64_t num) {
    printf("%" PRId64 "\n", num);
}

int main(void) {
    // puts("Hello, compy!");
    // TODO: in the future, allow accessing argc and argv via some runtime function
    compy_main();
    // puts("Goodbye, compy!");
    return 0;
}
