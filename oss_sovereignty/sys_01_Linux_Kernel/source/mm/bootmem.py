# Anvil Kernel: mm/bootmem.py
# Early boot memory allocator

_start_addr = 0x100000 # 1MB
_end_addr = 0x2000000  # 32MB (Arbitrary limit for prototype)
_current_ptr = _start_addr

def init():
    global _current_ptr
    _current_ptr = _start_addr
    print("[KERNEL] Bootmem initialized. Range: 0x{:x} - 0x{:x}".format(_start_addr, _end_addr))

def alloc(size):
    global _current_ptr
    if _current_ptr + size > _end_addr:
        print("[KERNEL] Bootmem: Out of memory!")
        return 0
    
    addr = _current_ptr
    _current_ptr += size
    return addr

def free(addr, size):
    # Bootmem doesn't usually support freeing in early stages
    pass
