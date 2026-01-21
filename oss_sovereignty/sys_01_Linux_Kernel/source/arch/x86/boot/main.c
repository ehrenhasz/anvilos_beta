#include "boot.h"
struct boot_params boot_params __attribute__((aligned(16)));struct port_io_ops pio_ops;char *HEAP;char *heap_end;void die(void){while(1);}void main(void){while(1);}