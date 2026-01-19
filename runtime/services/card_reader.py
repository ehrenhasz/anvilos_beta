#!/usr/bin/env python3
import time
import json
import subprocess
import os
import sys
from datetime import datetime

# Get the absolute path to the project root
# The script is in runtime/services/, so we go up two levels
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

QUEUE_FILE = os.path.join(PROJECT_ROOT, "runtime", "card_queue.json")
LOG_FILE = os.path.join(PROJECT_ROOT, "ext", "forge.log")

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass # Fail silently
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
    time.sleep(1)
    
    # Execute command if present
    command = card.get("command")
    result = "Processed (Manual/No-Op)"
    success = True
    
    if command:
        log(f"EXECUTING: {command}")
        try:
            # Run command in the project root
            proc = subprocess.run(
                command, 
                shell=True, 
                cwd=PROJECT_ROOT,
                capture_output=True, 
                text=True
            )
            if proc.returncode == 0:
                result = f"SUCCESS: {proc.stdout.strip()[:200]}..." # Truncate for log
            else:
                result = f"FAILURE: {proc.stderr.strip()}"
                log(f"ERROR: {result}")
                success = False
        except Exception as e:
            result = f"EXCEPTION: {str(e)}"
            log(f"CRITICAL: {result}")
            success = False
            
    log(f"RESULT: {result}")
    return success, result

def main():
    log(f"Card Reader Service Started (PID: {os.getpid()})")
    
    while True:
        queue = load_queue()
        modified = False
        target = None
        
        # Find next PENDING card
        # Filter for 'pending' or 'paused'
        # Sort by priority desc (if available) just in case
        pending_cards = [c for c in queue if c.get("status") in ["pending", "paused"]]
        if pending_cards:
            # Sort local list by priority
            pending_cards.sort(key=lambda x: x.get("priority", 50), reverse=True)
            target_id = pending_cards[0]["id"]
            
            # Find the actual index in the main queue to update
            for card in queue:
                if card["id"] == target_id:
                    target = card
                    break
        
        if target:
            # Mark processing
            target["status"] = "processing"
            target["started_at"] = datetime.now().isoformat()
            save_queue(queue)
            
            # Execute
            success, result = process_card(target)
            
            # Refresh queue to minimize race conditions
            queue = load_queue()
            for c in queue:
                if c["id"] == target["id"]:
                    c["status"] = "complete" if success else "failed"
                    c["completed_at"] = datetime.now().isoformat()
                    c["result"] = result
                    break
            save_queue(queue)
            modified = True
            
        if not modified:
            time.sleep(1)

if __name__ == "__main__":
    main()
