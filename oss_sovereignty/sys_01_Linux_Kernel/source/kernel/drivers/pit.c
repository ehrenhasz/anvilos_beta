#include "kernel.h"

void pit_init(uint16_t h) {
{__asm__ volatile("outb %%al, $0x43" :  : "a"(0x36) : );;__asm__ volatile("outb %%al, $0x40" :  : "a"((h&0xff)) : );;__asm__ volatile("outb %%al, $0x40" :  : "a"((h>>8)) : );}
}
