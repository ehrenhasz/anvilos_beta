# Minimal Anvil Kernel main entry point
# This is the first Anvil code that runs. Its goal is to initialize
# the bare minimum required to see output.

# We need to adjust the sys.path to find our kernel modules.
# In a real bootloader scenario, this would be handled by the
# Anvil environment setup.
import sys
# Assuming a flat kernel source for now.
# sys.path.append('/kernel') # This would be the ideal
# For now, we assume modules are in the same dir or accessible.
try:
    from kernel import printk
except ImportError:
    # This fallback is for development/testing and will not work
    # in a real kernel image. It allows us to run this file
    # directly if printk.mpy is in the same directory.
    import printk

def start_kernel():
    """
    This is the main entry point for the Anvil kernel.
    It replaces the `start_kernel` function in `init/main.c`.
    """
    # 1. Initialize the console driver.
    # This is the first and most critical step. Without a console,
    # we have no way of knowing if the kernel is alive.
    printk.early_init_console()

    # 2. Print a boot banner.
    # This signals that our Anvil code is executing.
    printk.printk("--- Anvil Kernel v0.1 ---")
    printk.printk("Copyright (C) 2026, The Committee")
    printk.printk("Booting ANVIL-OS...")

    # 3. Perform minimal, essential setups (placeholders for now).
    # In the future, we would call other init functions here, e.g.:
    # - trap_init()
    # - memory_init()
    # - sched_init()
    printk.printk("Performing critical initializations (stubs)...")

    # 4. Print the "Hello World" of kernels.
    printk.printk("HELLO SOVEREIGN")
    printk.printk("Initialization complete. Halting system.")

    # 5. Halt the system.
    # Since we have no scheduler, no idle thread, and no user space,
    # the only thing we can do is stop execution in an infinite loop.
    # This prevents the CPU from running off into undefined memory.
    while True:
        # In a real kernel, this might be a specific halt instruction
        # like `asm volatile("hlt")`. For Anvil, a tight loop is sufficient
        # to represent a halted state.
        pass

# This is the conventional way to make a Python file executable.
# In our kernel, the bootloader would call `start_kernel()` directly.
if __name__ == "__main__":
    start_kernel()
