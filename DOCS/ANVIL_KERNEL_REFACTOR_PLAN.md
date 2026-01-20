# Anvil Kernel Refactoring Plan

## Phase 1: Core Kernel Initialization (The "Smoke Test")

**Goal:** Achieve a minimal boot sequence where the Anvil-compiled kernel can print a message to the console. This phase focuses on the absolute bare minimum to prove the concept.

*   **Card 1.1:** Refactor `init/main.c` to `init/main.mpy`.
    *   **Task:** Translate the core `start_kernel()` logic.
    *   **Details:** Identify and stub out non-essential hardware initializations. The primary goal is to get to a point where `printk()` can be called.
    *   **Dependencies:** A functional Anvil `printk` equivalent.

*   **Card 1.2:** Refactor `kernel/printk/printk.c` to `kernel/printk.mpy`.
    *   **Task:** Create a basic logging mechanism that can write to the serial console.
    *   **Details:** This will be a simplified version of `printk`, without buffer management or complex formatting.
    *   **Dependencies:** Low-level serial driver access.

## Phase 2: Memory Management Primitives

**Goal:** Establish foundational memory management capabilities.

*   **Card 2.1:** Refactor `mm/bootmem.c` to `mm/bootmem.mpy`.
    *   **Task:** Implement the initial memory allocator used during boot.
    *   **Details:** Translate the logic for tracking and allocating physical memory before the primary slab allocator is available.

*   **Card 2.2:** Refactor `mm/page_alloc.c` to `mm/page_alloc.mpy`.
    *   **Task:** Implement the buddy allocator for physical page management.
    *   **Details:** This is a critical component and will require careful translation of the allocation and free logic.

*   **Card 2.3:** Refactor `mm/slab.c` to `mm/slab.mpy`.
    *   **Task:** Implement the slab allocator for kernel object caching.
    *   **Details:** Focus on the core logic for creating, growing, and shrinking caches.

## Phase 3: Architecture-Specific Code (x86_64)

**Goal:** Port the essential x86_64 architecture-specific code to Anvil.

*   **Card 3.1:** Refactor `arch/x86/boot/main.c` to `arch/x86/boot/main.mpy`.
    *   **Task:** Translate the very early boot code that runs before the kernel is fully operational.
    *   **Details:** This involves setting up the initial page tables and CPU state.

*   **Card 3.2:** Refactor `arch/x86/kernel/head_64.S` to `arch/x86/kernel/head_64.mpy`.
    *   **Task:** Translate the assembly code responsible for the initial jump into the 64-bit kernel.
    *   **Details:** This may require extending Anvil to support low-level assembly instructions or finding an alternative approach.

*   **Card 3.3:** Refactor `arch/x86/kernel/traps.c` to `arch/x86/kernel/traps.mpy`.
    *   **Task:** Implement basic trap and exception handlers.
    *   **Details:** This is crucial for debugging and handling hardware-level events.

## Phase 4: Filesystems (Minimal)

**Goal:** Implement a minimal in-memory filesystem to support basic user-space interaction.

*   **Card 4.1:** Refactor `fs/ramfs/inode.c` to `fs/ramfs/inode.mpy`.
    *   **Task:** Implement the core inode operations for a RAM-based filesystem.
    *   **Details:** Focus on creating, reading, and writing files in memory.

*   **Card 4.2:** Refactor `fs/dcache.c` to `fs/dcache.mpy`.
    *   **Task:** Implement the directory entry cache.
    *   **Details:** This is essential for filesystem performance and path lookups.

## Phase 5: Concurrency and IPC

**Goal:** Introduce basic concurrency and inter-process communication primitives.

*   **Card 5.1:** Refactor `kernel/sched/core.c` to `kernel/sched/core.mpy`.
    *   **Task:** Implement the core scheduler logic.
    *   **Details:** Start with a simple round-robin scheduler.

*   **Card 5.2:** Refactor `kernel/locking/mutex.c` to `kernel/locking/mutex.mpy`.
    *   **Task:** Implement mutexes for basic locking.
    *   **Details:** This is a prerequisite for any kind of safe concurrent operations.

*   **Card 5.3:** Refactor `ipc/pipe.c` to `ipc/pipe.mpy`.
    *   **Task:** Implement anonymous pipes for basic IPC.
    *   **Details:** This will allow for simple communication between processes.

---

This plan is a high-level overview. Each card will be broken down further into smaller, more granular tasks as we approach each phase.
