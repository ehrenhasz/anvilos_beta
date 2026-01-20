#include "kernel.h"

void fault_handler(uint8_t i, uint64_t e) {
__auto_type vga = Vga_new();Vga_write(&vga,0,0x46);Vga_write(&vga,1,0x41);Vga_write(&vga,2,0x55);Vga_write(&vga,3,0x4c);Vga_write(&vga,4,0x54);while(1){{__asm__ volatile("hlt" :  :  : );;}}
}
