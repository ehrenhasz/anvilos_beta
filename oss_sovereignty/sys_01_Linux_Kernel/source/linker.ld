ENTRY(_start)SECTIONS{.=0xffffffff80000000;.text:{*(.multiboot_header)*(.text)}.rodata:{*(.rodata)}.data:{*(.data)}.bss:{*(.bss)}}
