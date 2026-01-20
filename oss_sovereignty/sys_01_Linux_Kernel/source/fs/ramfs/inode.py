# Anvil Kernel: fs/ramfs/inode.py

class Inode:
    def __init__(self, mode):
        self.mode = mode
        self.size = 0
        self.data = bytearray()
        self.uid = 0
        self.gid = 0

    def read(self, offset, count):
        return self.data[offset:offset+count]

    def write(self, offset, data):
        end = offset + len(data)
        if end > len(self.data):
            self.data.extend(bytearray(end - len(self.data)))
        self.data[offset:end] = data
        self.size = len(self.data)
        return len(data)

def alloc_inode():
    return Inode(0o644)
