#include "kernel.h"

Serial Serial_new(uint16_t p) {
return (Serial){p};
}
void Serial_write(Serial* self, uint8_t b) {
{__asm__ volatile("outb %%al, %%dx" :  : "a"(b), "d"(self->p) : );}
}
