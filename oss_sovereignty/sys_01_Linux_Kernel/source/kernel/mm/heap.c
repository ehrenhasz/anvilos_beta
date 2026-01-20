#include "kernel.h"

uint64_t Heap_alloc(Heap* self, size_t size) {
__auto_type s = (uint64_t)size;if (self->used+s>self->size) {return 0;}else{__auto_type p = self->start+self->used;self->used+=s;return p;}
}
