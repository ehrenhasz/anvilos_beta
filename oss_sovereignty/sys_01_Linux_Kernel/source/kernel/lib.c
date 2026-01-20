#include "kernel.h"

void* memcpy(void* dst, const void* src, size_t n) {
__auto_type d = (uint8_t*)dst;__auto_type s = (const uint8_t*)src;size_t i = 0;while (i<n) {{d[i]=s[i];}i+=1;}return dst;
}
void* memset(void* dst, int32_t c, size_t n) {
__auto_type d = (uint8_t*)dst;size_t i = 0;while (i<n) {{d[i]=(uint8_t)c;}i+=1;}return dst;
}
