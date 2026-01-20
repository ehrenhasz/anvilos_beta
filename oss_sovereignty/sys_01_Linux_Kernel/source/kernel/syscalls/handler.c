#include "kernel.h"

uint64_t syscall_handler(uint64_t n, uint64_t a1, uint64_t a2) {
if (n==1) {/*print*/return 0;}else if (n==2) {/*exit*/return 0;}else{return 0;}
}
