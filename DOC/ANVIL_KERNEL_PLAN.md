# Anvil Kernel Transition Plan (Vertex Outline)

This document tracks the serial execution of recipes to transition from a standard Linux source tree to the custom Anvil kernel.

## Phase 1: The Great Purge (Environment & Assets)
- [x] **purge_foreign_architectures**: Iterate `arch/`, delete non-x86. Hard-lock to x86_64.
- [x] **purge_localization_files**: Recursive delete `.po`, `.mo`, locale dirs. Enforce English-only.
- [x] **sanitize_documentation**: `Documentation/` -> Keep only man/apropos sources.
- [x] **strip_kconfig_system**: Remove `scripts/kconfig`.
- [x] **remove_firmware_blobs**: Delete `firmware/`.

## Phase 2: The Anvil Bootstrap (Core Kernel Rewrite)
- [ ] **init_anvil_manifest**: Create root `anvil.toml` (target: x86_64-unknown-anvil-kernel).
- [ ] **transmute_entry_point**: Rewrite `arch/x86/boot/header.S` (Multiboot2, `_start`).
- [ ] **vga_buffer_driver**: Create `kernel/drivers/vga.anv` (0xb8000 wrapper).
- [ ] **serial_port_shim**: Create `kernel/drivers/serial.anv` (COM1 0x3F8).
- [ ] **gdt_rewrite**: Create `kernel/cpu/gdt.anv` (GDT implementation).
- [ ] **idt_structure**: Create `kernel/cpu/idt.anv` (IDT struct & interrupt wrapper).
- [ ] **pic_remap**: Create `kernel/cpu/pic.anv` (8259 PIC remapping).
- [ ] **cpu_exceptions**: Create `kernel/cpu/exceptions.anv` (Fault handlers).

## Phase 3: Memory Management (The Heavy Lifting)
- [ ] **physical_memory_map**: Create `kernel/mm/e820.anv` (Parse bootloader memory map).
- [ ] **paging_init**: Create `kernel/mm/paging.anv` (PML4, PDP, etc.).
- [ ] **kernel_heap_allocator**: Create `kernel/mm/heap.anv` (Bump/Linked-list allocator).

## Phase 4: Process Management
- [ ] **context_switch_asm**: Create `kernel/sched/switch.S` (Stack swap logic).
- [ ] **process_struct**: Create `kernel/sched/task.anv` (PCB: pid, state, stack_ptr, cr3).
- [ ] **pit_scheduler**: Create `kernel/drivers/pit.anv` (PIT config & scheduler yield).

## Phase 5: Input/Output & Filesystem
- [ ] **ps2_keyboard_poller**: Create `kernel/drivers/keyboard.anv` (Port 0x60, scancode table).
- [ ] **vfs_trait_definition**: Create `kernel/fs/vfs.anv` (File, Directory, Inode traits).
- [ ] **initramfs_parser**: Create `kernel/fs/initramfs.anv` (CPIO parser).

## Phase 6: Userland Support
- [ ] **syscall_dispatcher**: Create `kernel/syscalls/handler.anv` (MSR 0xC0000080 handler).
- [ ] **elf_loader**: Create `kernel/binfmt/elf.anv` (ELF64 parser & loader).
- [ ] **man_page_viewer**: Port minimal cat-like utility for man pages.

## Phase 7: Final Cleanup
- [ ] **strip_symbols**: Configure build to strip debug symbols.
- [ ] **final_link_script**: Create `linker.ld` (Kernel start: 0xffffffff80000000).
- [ ] **generate_iso_recipe**: Script to bundle kernel + man pages into ISO (xorriso/grub).