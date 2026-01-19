#!/usr/bin/env python3
import time
import json
import subprocess
import os
import sys
from datetime import datetime

QUEUE_FILE = "/home/aimeat/github/droppod/runtime/card_queue.json"
LOG_FILE = "/home/aimeat/github/droppod/ext/forge.log"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def load_queue():
    try:
        with open(QUEUE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_queue(queue):
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)

def process_card(card):
    log(f"PROCESSING CARD: {card.get('id')} - {card.get('description')}")
    
    # Simulate processing delay
    time.sleep(2)
    
    # Execute command if present
    command = card.get("command")
    result = "Processed (Manual/No-Op)"
    
    if command:
        log(f"EXECUTING: {command}")
        try:
            # Run command in the project root
            proc = subprocess.run(
                command, 
                shell=True, 
                cwd="/home/aimeat/github/droppod",
                capture_output=True, 
                text=True
            )
            if proc.returncode == 0:
                result = f"SUCCESS: {proc.stdout.strip()}"
            else:
                result = f"FAILURE: {proc.stderr.strip()}"
                log(f"ERROR: {result}")
                return False, result
        except Exception as e:
            result = f"EXCEPTION: {str(e)}"
            log(f"CRITICAL: {result}")
            return False, result
            
    log(f"RESULT: {result}")
    return True, result

def main():
    log(f"Card Reader Service Started (PID: {os.getpid()})")
    
    while True:
        queue = load_queue()
        modified = False
        
        # Find next PENDING or PAUSED card
        for card in queue:
            if card.get("status") in ["pending", "paused"]:
                # Mark as processing
                card["status"] = "processing"
                card["started_at"] = datetime.now().isoformat()
                save_queue(queue) # Save immediately to lock it
                
                # Execute
                success, result = process_card(card)
                
                # Update status
                # Reload queue to avoid overwriting new concurrent changes
                queue = load_queue()
                # Find the card again by ID (in case order shifted, though unlikely)
                for c in queue:
                    if c["id"] == card["id"]:
                        c["status"] = "complete" if success else "failed"
                        c["completed_at"] = datetime.now().isoformat()
                        c["result"] = result
                        break
                
                save_queue(queue)
                modified = True
                break # Process one at a time
        
        if not modified:
            time.sleep(1)

if __name__ == "__main__":
    main()
