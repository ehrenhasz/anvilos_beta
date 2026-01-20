#!/usr/bin/env python3
import sys
import os
import subprocess
import json
import sqlite3
import time

# --- PATH RESOLUTION ---
# agent_aimeat/aimeat.py is one level deep. Root is up one.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.append(os.path.join(PROJECT_ROOT, "runtime"))

from synapse import Synapse

def main():
    agent_id = "aimeat"
    synapse = Synapse(agent_id)
    print(f"[{agent_id}] Executor Online. Polling for jobs (Cortex DB)...")

    # Optional: Load API Key if we ever need to generate code dynamically
    # But for now, we execute strict shell commands or file writes defined by cards.
    
    processed_count = 0
    idle_count = 0

    while True:
        job = synapse.get_job()
        if not job:
            # If no jobs, wait a bit and retry (daemon mode) or exit?
            # User's previous execute_cards.py exited.
            # But "Executor Online" implies a daemon.
            # I will make it exit if no jobs found to match previous behavior, 
            # or maybe wait 5 seconds then exit if still empty?
            # The prompt said "quick boot and stop" earlier, but now "finall update".
            # I'll stick to: Run until empty, then exit.
            print(f"[{agent_id}] No pending jobs. Cooling down.")
            break
        
        idle_count = 0
        correlation_id = job['correlation_id']
        payload_str = job['payload']
        
        try:
            payload = json.loads(payload_str)
            command = payload.get('details')
            context = payload.get('context', 'unknown')
            job_type = payload.get('format', 'shell') # shell or recipe.py
            
            print(f"[{agent_id}] Processing: {context}")
            
            start_time = time.time()
            result_data = {}
            status = "FAILED"

            if job_type == "shell":
                print(f"  > Shell: {command}")
                process = subprocess.run(command, shell=True, capture_output=True, text=True)
                result_data = {
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "returncode": process.returncode
                }
                status = "COMPLETED" if process.returncode == 0 else "FAILED"
                
                if status == "FAILED":
                    print(f"  [ERROR] {process.stderr.strip()}")
                else:
                    print(f"  [OK] {process.stdout.strip()[:100]}...") # Truncate log

            elif job_type == "recipe.py":
                # If we need to run a python script content?
                # Or if the command is "python3 some_script.py" it falls under shell.
                # If 'details' IS the python code:
                print(f"  > Python Recipe Execution")
                try:
                    exec_globals = {}
                    exec(command, exec_globals)
                    result_data = {"output": "Executed Python Recipe"}
                    status = "COMPLETED"
                    print("  [OK] Recipe Executed")
                except Exception as e:
                    result_data = {"error": str(e)}
                    print(f"  [ERROR] {e}")

            else:
                result_data = {"error": f"Unknown format: {job_type}"}
                print(f"  [SKIP] Unknown format")

            # Log to DB
            synapse.update_job(correlation_id, status, result_data)
            
            # Log Experience
            synapse.log_experience(
                task_type="EXECUTION",
                context=context,
                success=(status == "COMPLETED"),
                details=result_data
            )
            
            if status == "FAILED":
                print(f"  [CRITICAL] Build/Execution failure detected.")
                print(f"  [MANDATE] Stopping all tasks. Protocol: Debug compiler at /usr/local/bin/anvil before resuming.")
                break
            
            processed_count += 1

        except Exception as e:
            print(f"[{agent_id}] Critical Job Error: {e}")
            synapse.update_job(correlation_id, "FAILED", {"error": str(e)})

    print(f"[{agent_id}] Session Finished. Jobs Processed: {processed_count}")

if __name__ == "__main__":
    main()