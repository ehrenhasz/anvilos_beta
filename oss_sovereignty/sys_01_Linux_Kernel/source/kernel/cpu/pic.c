#include "kernel.h"

void Pic_remap() {
{__asm__ volatile("outb %%al, $0x20;outb %%al, $0xa0;outb %%al, $0x21;outb %%al, $0xa1;outb %%al, $0x21;outb %%al, $0xa1;outb %%al, $0x21;outb %%al, $0xa1" :  : "a"(0x11) : );;__asm__ volatile("outb %%al, $0x21" :  : "a"(0x20) : );;__asm__ volatile("outb %%al, $0xa1" :  : "a"(0x28) : );;__asm__ volatile("outb %%al, $0x21" :  : "a"(4) : );;__asm__ volatile("outb %%al, $0xa1" :  : "a"(2) : );;__asm__ volatile("outb %%al, $0x21" :  : "a"(1) : );;__asm__ volatile("outb %%al, $0xa1" :  : "a"(1) : );;__asm__ volatile("outb %%al, $0x21" :  : "a"(0) : );;__asm__ volatile("outb %%al, $0xa1" :  : "a"(0) : );;}
}
