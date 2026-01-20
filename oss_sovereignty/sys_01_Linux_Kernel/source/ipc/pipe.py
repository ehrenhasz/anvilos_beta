# Anvil Kernel: ipc/pipe.py

class Pipe:
    def __init__(self):
        self.buffer = []
        self.readers = []
        self.writers = []

    def read(self):
        if self.buffer:
            return self.buffer.pop(0)
        return None

    def write(self, data):
        self.buffer.append(data)

def create_pipe():
    return Pipe()
