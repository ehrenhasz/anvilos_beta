#include "kernel.h"

void main() {
__auto_type vga = Vga_new();Vga_write(&vga,0,0x4f);Vga_write(&vga,1,0x4b);while(1){{__asm__ volatile("hlt" :  :  : );;}}
}
