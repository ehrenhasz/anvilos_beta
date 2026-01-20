.section .multiboot_header
.align 8
header_start:
    .long 0xe85250d6                /* magic */
    .long 0                         /* architecture: 0 (protected mode i386) */
    .long header_end - header_start /* header length */
    .long 0x100000000 - (0xe85250d6 + 0 + (header_end - header_start)) /* checksum */

    /* end tag */
    .short 0
    .short 0
    .long 8
header_end:

.section .text
.global _start
.type _start, @function
_start:
    cli
    mov $stack_top, %rsp
    call main
    hlt
.loop:
    jmp .loop

.section .bss
.align 16
stack_bottom:
.skip 16384
stack_top: