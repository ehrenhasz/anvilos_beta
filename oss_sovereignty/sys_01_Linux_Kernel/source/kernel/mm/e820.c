#include "kernel.h"

MemMap MemMap_parse(uint64_t p, size_t c) {
__auto_type m = (MemMap){.entries ={{0}},.count =c};{copy_nonoverlapping((const E820Entry*)p,m.entries,c);};
return m;
}
