#include "kernel.h"

uint8_t kbd_read() {
uint8_t b = 0;{__asm__ volatile("inb %%dx, %%al" : "=a"(b) : "d"(0x60) : );;};
return b;
}
