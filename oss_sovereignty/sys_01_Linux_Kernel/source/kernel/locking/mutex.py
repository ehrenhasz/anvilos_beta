# Anvil Kernel: kernel/locking/mutex.py

class Mutex:
    def __init__(self):
        self.locked = False
        self.owner = None

    def lock(self):
        # In a real kernel, this would block/sleep.
        # Here we just spin (dangerous in single thread) or check.
        if self.locked:
             # print("[LOCK] Contention!")
             pass
        self.locked = True

    def unlock(self):
        self.locked = False

def init_mutex(m):
    m.locked = False
