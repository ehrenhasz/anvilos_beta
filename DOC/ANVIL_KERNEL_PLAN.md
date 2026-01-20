# Anvil Kernel Transition Plan (Vertex Outline)

This document tracks the serial execution of recipes to transition from a standard Linux source tree to the custom Anvil kernel.

## DIRECTIVES (STRICT COMPLIANCE)
1.  **Code Style**: All `.anv` files must be **minified**. Remove all unnecessary whitespace/newlines. **NO COMMENTS** in code.
2.  **Format**: Use **MicroJSON** (RFC-0002) `{"@ID": int, "data": ...}` for all structured data and logs.
3.  **Evaluation**: Evaluate every module. If it is not critical for a bare-metal x86 boot, **DISCARD IT**.
4.  **Logging**: Every card execution must be logged to `cortex.db` with Pass/Fail status and MicroJSON details.

## Phase 1: The Great Purge (Environment & Assets)
- [x] **purge_foreign_architectures**: Iterate `arch/`, delete non-x86. Hard-lock to x86_64.
- [x] **purge_localization_files**: Recursive delete `.po`, `.mo`, locale dirs. Enforce English-only.
- [x] **sanitize_documentation**: `Documentation/` -> Keep only man/apropos sources.
- [x] **strip_kconfig_system**: Remove `scripts/kconfig`.
- [x] **remove_firmware_blobs**: Delete `firmware/`.

## Phase 2: The Anvil Bootstrap (Core Kernel Rewrite)
- [ ] **init_anvil_manifest**: Create `anvil.toml` (MicroJSON format if applicable). Target: `x86_64-unknown-anvil-kernel`.
- [ ] **transmute_entry_point**: Rewrite `arch/x86/boot/header.S`. Minimal Multiboot2, `_start`. No comments.
- [ ] **vga_buffer_driver**: Create `kernel/drivers/vga.anv`. 0xb8000 wrapper. Minified.
- [ ] **serial_port_shim**: Create `kernel/drivers/serial.anv`. COM1 0x3F8. Minified.
- [ ] **gdt_rewrite**: Create `kernel/cpu/gdt.anv`. GDT implementation. Minified.
- [ ] **idt_structure**: Create `kernel/cpu/idt.anv`. IDT struct & interrupt wrapper. Minified.
- [ ] **pic_remap**: Create `kernel/cpu/pic.anv`. 8259 PIC remapping. Minified.
- [ ] **cpu_exceptions**: Create `kernel/cpu/exceptions.anv`. Fault handlers. Minified.

## Phase 3: Memory Management (The Heavy Lifting)
- [ ] **physical_memory_map**: Create `kernel/mm/e820.anv`. Parse bootloader map. STRICT EVALUATION: Only keep usable RAM regions.
- [ ] **paging_init**: Create `kernel/mm/paging.anv`. PML4, PDP. Minified.
- [ ] **kernel_heap_allocator**: Create `kernel/mm/heap.anv`. Basic allocator. Minified.

## Phase 4: Process Management
- [ ] **context_switch_asm**: Create `kernel/sched/switch.S`. Stack swap. Minified asm.
- [ ] **process_struct**: Create `kernel/sched/task.anv`. PCB (pid, state, stack, cr3). Minified.
- [ ] **pit_scheduler**: Create `kernel/drivers/pit.anv`. PIT config. Minified.

## Phase 5: Input/Output & Filesystem
- [ ] **ps2_keyboard_poller**: Create `kernel/drivers/keyboard.anv`. Port 0x60. Minified.
- [ ] **vfs_trait_definition**: Create `kernel/fs/vfs.anv`. Trait defs only. Minified.
- [ ] **initramfs_parser**: Create `kernel/fs/initramfs.anv`. CPIO parser. Minified.

## Phase 6: Userland Support
- [ ] **syscall_dispatcher**: Create `kernel/syscalls/handler.anv`. MSR 0xC0000080. Minified.
- [ ] **elf_loader**: Create `kernel/binfmt/elf.anv`. ELF64 loader. Minified.
- [ ] **man_page_viewer**: Port minimal cat-like utility. Minified.

## Phase 7: Final Cleanup
- [ ] **strip_symbols**: Configure build to strip all symbols.
- [ ] **final_link_script**: Create `linker.ld`. Minified.
- [ ] **generate_iso_recipe**: Script to bundle ISO.