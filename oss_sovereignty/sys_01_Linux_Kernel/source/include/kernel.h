#ifndef ANVIL_KERNEL_H
#define ANVIL_KERNEL_H
#include <stdint.h>
#include <stddef.h>
#define copy_nonoverlapping(src, dst, count) __builtin_memcpy(dst, src, (count) * sizeof(*(src)))

typedef struct ElfHeader ElfHeader;
typedef struct Pic Pic;
typedef struct IdtEntry IdtEntry;
typedef struct IdtPtr IdtPtr;
typedef struct GdtEntry GdtEntry;
typedef struct GdtPtr GdtPtr;
typedef struct Task Task;
typedef struct CpioHeader CpioHeader;
typedef struct Heap Heap;
typedef struct E820Entry E820Entry;
typedef struct MemMap MemMap;
typedef struct Vga Vga;
typedef struct Serial Serial;
struct ElfHeader {
    uint8_t m[4];
    uint8_t cl;
    uint8_t d;
    uint8_t v;
    uint8_t os;
    uint8_t abiv;
    uint8_t p[7];
    uint16_t t;
    uint16_t mac;
    uint32_t ver;
    uint64_t e;
    uint64_t ph;
    uint64_t sh;
    uint32_t f;
    uint16_t hs;
    uint16_t ps;
    uint16_t pc;
    uint16_t ss;
    uint16_t sc;
    uint16_t si;
};
struct Pic {
    uint16_t m;
    uint16_t s;
};
struct IdtEntry {
    uint16_t o_l;
    uint16_t s;
    uint8_t i;
    uint8_t t;
    uint16_t o_m;
    uint32_t o_h;
    uint32_t r;
};
struct IdtPtr {
    uint16_t l;
    uint64_t b;
};
struct GdtEntry {
    uint16_t l;
    uint16_t b_l;
    uint8_t b_m;
    uint8_t a;
    uint8_t f;
    uint8_t b_h;
};
struct GdtPtr {
    uint16_t limit;
    uint64_t base;
};
struct Task {
    uint64_t rsp;
    uint64_t cr3;
    uint32_t pid;
    uint8_t state;
};
struct CpioHeader {
    uint16_t m;
    uint16_t d;
    uint16_t i;
    uint16_t mde;
    uint16_t u;
    uint16_t g;
    uint16_t nl;
    uint32_t mt;
    uint32_t sz;
    uint16_t nm;
};
struct Heap {
    uint64_t start;
    uint64_t size;
    uint64_t used;
};
struct E820Entry {
    uint64_t base;
    uint64_t len;
    uint32_t typ;
    uint32_t ext;
};
struct MemMap {
    E820Entry entries[128];
    size_t count;
};
struct Vga {
    uint8_t* p;
};
struct Serial {
    uint16_t p;
};
void main();
void* memcpy(void* dst, const void* src, size_t n);
void* memset(void* dst, int32_t c, size_t n);
void main();
void Pic_remap();
void fault_handler(uint8_t i, uint64_t e);
uint64_t syscall_handler(uint64_t n, uint64_t a1, uint64_t a2);
uint64_t Heap_alloc(Heap* self, size_t size);
MemMap MemMap_parse(uint64_t p, size_t c);
void pit_init(uint16_t h);
Vga Vga_new();
void Vga_write(Vga* self, size_t i, uint8_t b);
Serial Serial_new(uint16_t p);
void Serial_write(Serial* self, uint8_t b);
uint8_t kbd_read();
#endif
