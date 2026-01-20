#!/usr/bin/env python3
import sys
import os
import subprocess
import json
import sqlite3
import time
import shutil

# --- PATH RESOLUTION ---
# agent_aimeat/aimeat.py is one level deep. Root is up one.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.append(os.path.join(PROJECT_ROOT, "runtime"))

from synapse import Synapse

def main():

    agent_id = "aimeat"

    print(f"[{agent_id}] Executor Online. Reading mission from ANVIL_KERNEL_REFACTOR_PLAN.md...")

    # --- Configuration ---

    refactor_plan_path = os.path.join(PROJECT_ROOT, "DOCS", "ANVIL_KERNEL_REFACTOR_PLAN.md")
    state_file_path = os.path.join(PROJECT_ROOT, "agent_aimeat", "state.json")
    
    # Updated Compiler Path to mpy-cross
    compiler_path = os.path.join(PROJECT_ROOT, "oss_sovereignty", "sys_09_Anvil", "source", "mpy-cross", "build", "mpy-cross")
    
    # Root of the kernel source where operations happen
    kernel_source_root = os.path.join(PROJECT_ROOT, "oss_sovereignty", "sys_01_Linux_Kernel", "source")

    # --- Pre-flight Checks ---

    if not os.path.exists(compiler_path):
        print(f"  [CRITICAL] Anvil compiler (mpy-cross) not found at: {compiler_path}")
        print(f"  Please ensure the toolchain is built and in the correct location.")
        return

    if not os.path.exists(kernel_source_root):
        print(f"  [CRITICAL] Kernel source not found at: {kernel_source_root}")
        return

    # --- State and Plan Loading ---

    def read_plan(path):
        with open(path, 'r') as f:
            return f.readlines()

    def parse_task_line(line):
        # Expected format: "*   **Card X.Y:** Refactor <source> to <dest>."
        try:
            # Remove markdown bold/formatting to simplify parsing
            clean_line = line.replace("*", "").replace("`", "").strip()
            # Example clean: "Card 1.1: Refactor init/main.c to init/main.mpy."
            
            if not clean_line.startswith("Card"):
                return None

            parts = clean_line.split(":")
            card_id = parts[0].strip()
            instruction = parts[1].strip() # "Refactor init/main.c to init/main.mpy."
            
            if "Refactor" in instruction and "to" in instruction:
                # remove "Refactor" and trailing "."
                instruction = instruction.replace("Refactor", "").rstrip(".")
                src_path, dst_path = instruction.split(" to ")
                return {
                    "raw": line.strip(),
                    "id": card_id,
                    "src": src_path.strip(),
                    "dst": dst_path.strip()
                }
        except Exception as e:
            print(f"  [WARN] Failed to parse line '{line.strip()}': {e}")
            return None
        return None

    def load_state(path):
        if not os.path.exists(path):
            save_state(path, {"completed_tasks": []})
        with open(path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"completed_tasks": []}

    def save_state(path, state):
        with open(path, 'w') as f:
            json.dump(state, f, indent=4)

    plan_lines = read_plan(refactor_plan_path)
    tasks = []
    for line in plan_lines:
        task_info = parse_task_line(line)
        if task_info:
            tasks.append(task_info)

    state = load_state(state_file_path)
    
    print(f"Found {len(tasks)} tasks in the plan.")

    # --- Task Execution Loop ---

    for task in tasks:
        task_raw = task["raw"]
        if task_raw in state["completed_tasks"]:
            print(f"  [SKIP] Task already completed: {task["id"]}")
            continue

        print(f"  [TODO] Processing {task['id']}: Refactor {task['src']} -> {task['dst']}")
        
        # Resolve absolute paths
        # Note: The plan paths are relative to the kernel source root
        src_abs = os.path.join(kernel_source_root, task["src"])
        dst_abs = os.path.join(kernel_source_root, task["dst"])
        
        # Logic: 
        # The Goal is to produce dst_abs (executable bytecode .mpy).
        # We need a python source file (.py) to compile.
        # Check if dst_abs already exists.
        
        python_source_abs = dst_abs.replace(".mpy", ".py")
        
        compile_needed = False
        
        if os.path.exists(dst_abs):
            # Check if it's binary or text
            is_binary = False
            try:
                with open(dst_abs, 'rb') as f:
                    chunk = f.read(1024)
                    if b'\0' in chunk:
                        is_binary = True
            except:
                pass

            if not is_binary:
                print(f"    > Found text content in target {task['dst']}. Converting to source (.py)...")
                shutil.move(dst_abs, python_source_abs)
                print(f"    > Renamed to {os.path.basename(python_source_abs)}")
                compile_needed = True
            else:
                print(f"    > Target {task['dst']} exists and is binary. Verifying...")
                # Assuming it's done, but we could re-compile if source exists and is newer.
                if os.path.exists(python_source_abs):
                     compile_needed = True # Re-compile to be safe/update
                else:
                    print(f"    > Binary exists and no source found. Marking complete.")
                    state["completed_tasks"].append(task_raw)
                    save_state(state_file_path, state)
                    continue

        elif os.path.exists(python_source_abs):
            print(f"    > Found Python source: {os.path.basename(python_source_abs)}")
            compile_needed = True
        else:
            print(f"    > [MISSING] No Python source found for {task['dst']}")
            print(f"    > Waiting for manual/AI translation of {task['src']}")
            continue

        if compile_needed:
            print(f"    > Compiling {os.path.basename(python_source_abs)} to .mpy ...")
            # mpy-cross <source> -o <dest>
            # Note: mpy-cross output defaults to source.mpy if -o not specified? 
            # Let's specify -o for safety
            
            command = [compiler_path, python_source_abs, "-o", dst_abs]
            
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  [OK] Compilation successful: {task['dst']}")
                state["completed_tasks"].append(task_raw)
                save_state(state_file_path, state)
            else:
                print(f"  [ERROR] Compilation failed for {task['id']}")
                print(f"    > STDERR: {result.stderr.strip()}")
                break # Stop on error

    print(f"[{agent_id}] Refactor plan execution finished.")
    
    # --- Synapse Job Processing ---
    print(f"[{agent_id}] Connecting to Synapse (Cortex DB) for additional missions...")
    synapse = Synapse(agent_id)
    
    while True:
        job = synapse.get_job()
        if not job:
            print(f"[{agent_id}] No more jobs in Cortex.")
            break
            
        print(f"  [JOB] Received: {job['correlation_id']} - {json.loads(job['payload'])['description']}")
        
        try:
            payload = json.loads(job['payload'])
            
            if payload.get('format') == 'recipe.py':
                script_content = payload['details']
                print(f"    > Executing recipe...")
                
                recipe_path = os.path.join(PROJECT_ROOT, f"recipe_{job['correlation_id']}.py")
                with open(recipe_path, 'w') as f:
                    f.write(script_content)
                
                proc = subprocess.run(["python3", recipe_path], capture_output=True, text=True)
                
                if proc.returncode == 0:
                    print(f"    > [SUCCESS] {proc.stdout.strip()}")
                    synapse.update_job(job['correlation_id'], "COMPLETED", "Executed successfully")
                else:
                    print(f"    > [FAILED] {proc.stderr.strip()}")
                    synapse.update_job(job['correlation_id'], "FAILED", proc.stderr.strip())
                
                # Cleanup
                if os.path.exists(recipe_path):
                    os.remove(recipe_path)

            elif payload.get('format') == 'shell':
                command = payload['details']
                print(f"    > Executing shell command: {command}")
                
                proc = subprocess.run(command, shell=True, capture_output=True, text=True)
                
                if proc.returncode == 0:
                    print(f"    > [SUCCESS] {proc.stdout.strip()}")
                    synapse.update_job(job['correlation_id'], "COMPLETED", "Executed successfully")
                else:
                    print(f"    > [FAILED] {proc.stderr.strip()}")
                    synapse.update_job(job['correlation_id'], "FAILED", proc.stderr.strip())

            else:
                print(f"    > [WARN] Unknown job format: {payload.get('format')}")
                synapse.update_job(job['correlation_id'], "FAILED", "Unknown format")
                
        except Exception as e:
            print(f"    > [ERROR] Processing failed: {e}")
            synapse.update_job(job['correlation_id'], "FAILED", str(e))

if __name__ == "__main__":
    main()
