# Anvil Kernel: arch/x86/kernel/head_64.py
# Entry point for 64-bit kernel

def entry_64():
    print("[ARCH] Entering 64-bit Long Mode")
    print("[ARCH] Initializing stack...")
    
    # Jump to generic kernel init
    try:
        from init import main
        main.start_kernel()
    except ImportError:
        print("[ARCH] FATAL: Could not load init/main.mpy")
        while True: pass

if __name__ == "__main__":
    entry_64()
