#include "kernel.h"

Vga Vga_new() {
__auto_type p = (uint8_t*)0xb8000;return (Vga){p};
}
void Vga_write(Vga* self, size_t i, uint8_t b) {
{self->p[i*2]=b;self->p[i*2+1]=0x0f;}
}
