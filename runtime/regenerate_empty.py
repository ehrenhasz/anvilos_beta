import os
import json
import uuid
from datetime import datetime
from generate_clone_cards import REPO_MAP, create_card

OSS_DIR = "oss_sovereignty"
QUEUE_DIR = "cards/queue"

def is_dir_empty(path):
    # Check if directory is empty (ignoring . and ..)
    if not os.path.exists(path):
        return True
    return len(os.listdir(path)) == 0

def main():
    dirs = [d for d in os.listdir(OSS_DIR) if os.path.isdir(os.path.join(OSS_DIR, d))]
    print(f"Checking {len(dirs)} directories...")
    
    count = 0
    for d in dirs:
        path = os.path.join(OSS_DIR, d)
        if is_dir_empty(path):
            if d in REPO_MAP:
                print(f"Found EMPTY directory with Repo Map: {d}")
                create_card(d, REPO_MAP[d])
                count += 1
            else:
                print(f"Skipping EMPTY directory {d} (No URL in REPO_MAP)")
    
    print(f"Generated {count} retry cards.")

if __name__ == "__main__":
    main()
