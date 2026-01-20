# Anvil Kernel: arch/x86/kernel/traps.py

def trap_handler(vector, error_code=0):
    print(f"[TRAP] CPU Exception Vector: {vector} Error: {error_code}")
    if vector == 14:
        print("[TRAP] Page Fault!")
    # Halt for now
    while True: pass

def init_traps():
    print("[ARCH] IDT Initialized (Traps ready)")
