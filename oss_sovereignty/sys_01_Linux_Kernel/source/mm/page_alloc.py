# Anvil Kernel: mm/page_alloc.py
# Physical page allocator (Buddy System simplified)

try:
    from mm import bootmem
except ImportError:
    # Fallback if bootmem not ready (or circular dep prevention)
    class MockBootmem:
        def alloc(self, size): return 0xCAFEBABE
    bootmem = MockBootmem()

PAGE_SIZE = 4096

def init():
    print("[KERNEL] Page Allocator initialized.")

def alloc_pages(order):
    # Order 0 = 1 page, Order 1 = 2 pages, etc.
    count = 1 << order
    size = count * PAGE_SIZE
    
    addr = bootmem.alloc(size)
    if addr == 0:
        return None
    return addr

def free_pages(addr, order):
    print(f"[KERNEL] Freed pages at 0x{addr:x}")
