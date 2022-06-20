#include "common.h"

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
