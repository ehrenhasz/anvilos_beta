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
- [x] **init_anvil_manifest**: Create `anvil.toml` (MicroJSON format if applicable). Target: `x86_64-unknown-anvil-kernel`.
- [x] **transmute_entry_point**: Rewrite `arch/x86/boot/header.S`. Minimal Multiboot2, `_start`. No comments.
- [x] **vga_buffer_driver**: Create `kernel/drivers/vga.anv`. 0xb8000 wrapper. Minified.
- [x] **serial_port_shim**: Create `kernel/drivers/serial.anv`. COM1 0x3F8. Minified.
- [x] **gdt_rewrite**: Create `kernel/cpu/gdt.anv`. GDT implementation. Minified.
- [x] **idt_structure**: Create `kernel/cpu/idt.anv`. IDT struct & interrupt wrapper. Minified.
- [x] **pic_remap**: Create `kernel/cpu/pic.anv`. 8259 PIC remapping. Minified.
- [x] **cpu_exceptions**: Create `kernel/cpu/exceptions.anv`. Fault handlers. Minified.

## Phase 3: Memory Management (The Heavy Lifting)
- [x] **physical_memory_map**: Create `kernel/mm/e820.anv`. Parse bootloader map. STRICT EVALUATION: Only keep usable RAM regions.
- [x] **paging_init**: Create `kernel/mm/paging.anv`. PML4, PDP. Minified.
- [x] **kernel_heap_allocator**: Create `kernel/mm/heap.anv`. Basic allocator. Minified.

## Phase 4: Process Management
- [x] **context_switch_asm**: Create `kernel/sched/switch.S`. Stack swap. Minified asm.
- [x] **process_struct**: Create `kernel/sched/task.anv`. PCB (pid, state, stack, cr3). Minified.
- [x] **pit_scheduler**: Create `kernel/drivers/pit.anv`. PIT config. Minified.

## Phase 5: Input/Output & Filesystem
- [x] **ps2_keyboard_poller**: Create `kernel/drivers/keyboard.anv`. Port 0x60. Minified.
- [x] **vfs_trait_definition**: Create `kernel/fs/vfs.anv`. Trait defs only. Minified.
- [x] **initramfs_parser**: Create `kernel/fs/initramfs.anv`. CPIO parser. Minified.

## Phase 6: Userland Support
- [x] **syscall_dispatcher**: Create `kernel/syscalls/handler.anv`. MSR 0xC0000080. Minified.
- [x] **elf_loader**: Create `kernel/binfmt/elf.anv`. ELF64 loader. Minified.
- [x] **man_page_viewer**: Port minimal cat-like utility. Minified.

## Phase 7: Final Cleanup
- [x] **strip_symbols**: Configure build to strip all symbols.
- [x] **final_link_script**: Create `linker.ld`. Minified.
- [x] **generate_iso_recipe**: Script to bundle ISO.

## Phase 8: AI Machine Code Integration (RFC-0009)
- [x] **compile_sovereign_compiler**: Build `mpy-cross` as the Anvil Compiler.
- [x] **freeze_agent_logic**: Compile `agent.py` into `agent.mpy` bytecode.
- [x] **deploy_static_vm**: Verify execution via lobotomized `micropython` binary.

## Phase 9: Cortex Genesis Protocol (RFC-0011)
- [x] **init_cortex_schema**: Provision `cortex.db` with Sector A-D lobes.
- [x] **bootstrap_genesis_bootloader**: Create `/bin/genesis` to pull soul from Cortex.
- [x] **crystallize_source**: Ingest all `.anv` and `.S` artifacts into `forge_artifacts`.

## Phase 10: ZFS Integration (RFC-0026)
- [x] **assimilate_zfs_source**: Add OpenZFS source to `oss_sovereignty`.
- [ ] **compile_zfs_tools**: Create recipes for cross-compiling ZFS userspace utilities.
- [ ] **integrate_zfs_kernel**: Statically compile ZFS kernel module into the Anvil kernel.
- [ ] **create_zfs_image_recipe**: Implement the Transitional Protocol for creating a ZFS image from the `ext4` host.
- [ ] **update_iso_recipe**: Modify the ISO generation script to use the ZFS root image.

## Phase 11: Shell Standardization (RFC-0027)
- [ ] **assimilate_bash**: Add GNU Bash source to `oss_sovereignty`.
- [ ] **assimilate_micropython**: Ensure MicroPython source is assimilated for userland `python`.
- [ ] **configure_kernel_shells**: Modify kernel config to only support required shell interfaces.
- [ ] **purge_unauthorized_shells**: Implement build steps to remove all blacklisted shell binaries.
- [ ] **validate_final_shells**: Add a final validation step to ensure only `bash` and `python` executables are present.



