#include "common.h"
#include "string.h"

typedef const char * const const_str_t;

static const_str_t type_names[] = {
    "int",
    "NoneType",
    "type",
    "bool"
};

const type_t NUM_TYPES = sizeof(type_names) / sizeof(const_str_t);

const char *to_typename(type_t type) {
    assertm(type < NUM_TYPES, "to_typename: Invalid type code");
    return type_names[type];
}

type_t from_typename(const char *name) {
    for (type_t t = 0; t < NUM_TYPES; t++) {
        if (!strcmp(type_names[t], name)) {
            return t;
        }
    }
    return TYPE_INVALID;
}
