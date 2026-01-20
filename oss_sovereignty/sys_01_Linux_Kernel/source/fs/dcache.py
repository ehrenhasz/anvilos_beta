# Anvil Kernel: fs/dcache.py

_dentry_cache = {}

def d_lookup(parent, name):
    key = (parent, name)
    return _dentry_cache.get(key)

def d_add(parent, name, inode):
    key = (parent, name)
    _dentry_cache[key] = inode

def d_init():
    print("[FS] Dentry Cache Initialized")
