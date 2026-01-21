#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import time
import sqlite3

# Try to import google genai, but don't crash if missing (we are focusing on Kernel Plan)
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None
    print("[WARN] google.genai library not found. Agent mode limited.")

# --- PATH RESOLUTION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = CURRENT_DIR
sys.path.append(os.path.join(PROJECT_ROOT, "runtime"))

from synapse import Synapse
from collar import TheCollar

TOKEN_PATH = os.path.join(CURRENT_DIR, "config", "token")

# --- SOVEREIGN CONFIG ---
CONFIG = {
    "AGENT_ID": "aimeat",
    "IDENTITY": "The Operator",
    "MODEL_ID": "gemini-2.0-flash"
}

SYNAPSE = Synapse(CONFIG["AGENT_ID"])
COLLAR = TheCollar(CONFIG["AGENT_ID"])

# --- AUTHENTICATION (INJECTED) ---
TOKEN_PATH = os.path.join(PROJECT_ROOT, "agent_ladysmith", "token")
API_KEY = os.environ.get("GEMINI_API_KEY")
try:
    if not API_KEY and os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'r') as f:
            API_KEY = f.read().strip()
    
    if not API_KEY:
        API_KEY = os.environ.get("GOOGLE_API_KEY")

except Exception as e:
    print(f"[WARN] Auth load issue: {e}")

# --- DB HELPERS ---
def log_ujson(id_code, data):
    print(json.dumps({"@ID": id_code, "data": data}))

# --- ENTRY POINT LOGIC ---
def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
    else:
        cmd = "boot"

    if cmd == "boot":
        print(f"aimeat: {fast_boot()}")
    elif cmd == "init":
        print(f"aimeat: {fast_boot()}")
    elif cmd == "work":
        print(f"aimeat: {process_jobs()}")
    elif cmd == "agent":
        run_agent()
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: aimeat.py [init|boot|work|agent]")

# --- BEGIN BOOT SEQUENCE (PROTECTED) ---
def fast_boot():
    """
    State-First Boot: Pulls identity from Cortex DB, logs to temp, no filesystem crawling.
    """
    boot_log_path = "/mnt/anvil_temp/boot.log"
    # Ensure temp dir exists if possible, otherwise skip logging to file
    try:
        os.makedirs(os.path.dirname(boot_log_path), exist_ok=True)
    except OSError:
        pass # Ignore permission errors in temp
    
    try:
        # Direct DB pull for speed and truth
        cortex_db_path = os.path.join(PROJECT_ROOT, "runtime", "cortex.db")
        
        identity = CONFIG["IDENTITY"]
        status = "OFFLINE"
        coding_id = CONFIG["AGENT_ID"].upper() if "MEAT" not in CONFIG["AGENT_ID"].upper() else "MEAT"
        
        # 1. State-First Validation (Read Only if possible, or very fast)
        # We ensure the agents table exists.
        with sqlite3.connect(cortex_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS agents (agent_id TEXT PRIMARY KEY, status TEXT, updated_at DATETIME, coding_id TEXT)")
            conn.commit()
            status = "READY"
        
        # 2. Prepare Boot Artifact
        boot_data = {
            "agent": CONFIG["AGENT_ID"],
            "identity": identity,
            "coding_id": coding_id,
            "mode": "STATE_FIRST",
            "status": status,
            "temp_ready": os.path.exists("/mnt/anvil_temp")
        }
        
        # 3. MicroJSON Log to Standard Out (RFC-0002)
        log_ujson(100, boot_data)
        
        # 4. Finalize Presence via Collar (Ensures persistent sync)
        COLLAR.log("BOOT_SEQUENCE", "fast_boot", True, boot_data)

        # 5. RESUME PLAN (NEW - Added for Kernel Plan Persistence)
        active_plan = SYNAPSE.get_active_plan()
        if active_plan:
            plan_name = active_plan['plan_name']
            step = active_plan['current_step']
            print(f"\n>> [RESUMING OPERATION]: PLAN '{plan_name}' | STEP {step}")
            COLLAR.log("PLAN_RESUME", "fast_boot", True, {"plan": plan_name, "step": step})
        
        # 6. COGNITIVE RESURRECTION (NEW - Smarter Boot)
        snap, ts = SYNAPSE.load_snapshot()
        if snap:
            print(f">> [RESURRECTION]: Restoring Context from {ts}")
            # In a real implementation, we would re-hydrate the LLM context here.
            # For now, we just acknowledge it.
            COLLAR.log("MIND_RESTORE", "fast_boot", True, {"timestamp": ts})
        else:
            print("\n>> [NO ACTIVE PLAN]: Waiting for instructions.")

        return "ONLINE"

    except Exception as e:
        err_data = {"error": str(e), "trace": "aimeat.py:fast_boot"}
        log_ujson(500, err_data)
        COLLAR.log("BOOT_FAILURE", "fast_boot", False, err_data)
        return f"FAILURE: {str(e)}"
# --- END BOOT SEQUENCE ---

def process_jobs():
    try:
        job = SYNAPSE.get_job()
        if not job:
            return "NO_JOBS"
        
        job_id = job["correlation_id"]
        
        try:
            raw_payload = json.loads(job["payload"])
            # Unwrap list if necessary (consistency with BigIron fix)
            if isinstance(raw_payload, list) and len(raw_payload) > 0:
                payload = raw_payload[0]
            else:
                payload = raw_payload

            log_ujson(200, {"job": job_id, "status": "STARTING", "desc": payload.get("description")})
            
            fmt = payload.get("format")
            result_output = ""
            success = False

            if fmt == "recipe.py":
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                    tmp.write(payload["details"])
                    tmp_path = tmp.name
                
                cmd_res = COLLAR.sh(f"{sys.executable} {tmp_path}", context=f"JOB_{job_id}")
                os.remove(tmp_path)
                
                success = (cmd_res.returncode == 0)
                result_output = cmd_res.stdout if success else cmd_res.stderr
            
            elif fmt == "shell":
                cmd = payload["details"]
                # Force /bin/bash for 'source' compatibility
                cmd_res = subprocess.run(cmd, shell=True, cwd=PROJECT_ROOT, capture_output=True, text=True, executable='/bin/bash')
                success = (cmd_res.returncode == 0)
                result_output = cmd_res.stdout if success else cmd_res.stderr
            
            else:
                raise ValueError(f"Unknown format: {fmt}")

            status = "COMPLETED" if success else "FAILED"
            SYNAPSE.update_job(job_id, status, result_output)
            
            # Save state after job
            SYNAPSE.save_snapshot({"last_job": job_id, "status": status})
            
            return f"PROCESSED {job_id}: {status}"
            
        except Exception as e:
            SYNAPSE.update_job(job_id, "FAILED", str(e))
            COLLAR.log("JOB_CRASH", job_id, False, {"error": str(e)})
            return f"CRASH {job_id}: {str(e)}"
            
    except Exception as e:
        return f"SYNAPSE_ERROR: {str(e)}"

# --- CORE: KNOWLEDGE INJECTION ---
def load_knowledge_base():
    """
    Loads critical RFCs to ground the Agent in the Titanium Law.
    """
    kb = []
    rfc_dir = os.path.join(PROJECT_ROOT, "DOCS", "RFC")
    # Priority RFCs
    priority_files = [
        "RFC-2026-000003-THE-ANVIL.txt",
        "RFC-2026-000009-SOVEREIGN-COMPILER.txt",
        "RFC-2026-000011-THE-CORTEX.txt",
        "RFC-2026-000000-GOVERNANCE.txt"
    ]
    
    kb.append("--- TITANIUM LAW (CORE KNOWLEDGE) ---")
    
    for filename in priority_files:
        path = os.path.join(rfc_dir, filename)
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    content = f.read()
                    kb.append(f"=== {filename} ===\n{content}\n")
            except Exception as e:
                print(f"[WARN] Failed to load {filename}: {e}")
    
    return "\n".join(kb)

# --- CORE: AGENT TOOLS ---
def submit_ops_cycle(job_type: str, context: str, payload: str, correlation_id: str = None):
    """
    Submits a High-Level Task to the Cortex.
    Status: NEEDS_CODING -> Picked up by Ladysmith -> Processed to PENDING -> Executed by BigIron.
    """
    if not correlation_id:
        correlation_id = f"aimeat-{int(time.time())}"

    if job_type not in ["CODE_CHANGE", "SYSTEM_OP"]:
        return {"status": "FAILURE", "error": "Invalid job_type."}

    try:
        # Construct the "Intent" Payload
        card_data = {
            "type": job_type,
            "context": context,
            "description": payload, # The "Prompt" for Ladysmith
            "source": "AIMEAT",
            "instruction": "WAIT_FOR_LADYSMITH" # Marker
        }
        
        # Insert directly into Cortex via Synapse (The Nerve)
        # We assume SYNAPSE is globally available (it is initialized at top of file)
        with SYNAPSE._get_cortex_conn() as conn:
            conn.execute("""
                INSERT INTO jobs (correlation_id, idempotency_key, priority, cost_center, payload, status)
                VALUES (?, ?, ?, ?, ?, 'NEEDS_CODING')
            """, (correlation_id, f"op-{correlation_id}", 50, "AIMEAT", json.dumps(card_data)))
            conn.commit()

        COLLAR.log("CARD_POSTED", correlation_id, True, {"status": "NEEDS_CODING", "task": payload})
        return {"status": "SUCCESS", "output": f"Card {correlation_id} posted to Queue. Awaiting Ladysmith."}

    except Exception as e:
        COLLAR.log("CARD_REJECTED", correlation_id, False, {"error": str(e)})
        return {"status": "CRITICAL_ERROR", "error": str(e)}

# --- CORE: INTERACTIVE AGENT ---
def run_agent():
    if not API_KEY:
        print("[ERROR] No API Key found in 'token' file or env.")
        return

    if not genai:
        print("[ERROR] google.genai not installed. Cannot run interactive agent.")
        return

    print(f"IDENTITY: {CONFIG['AGENT_ID']} | MODEL: {CONFIG['MODEL_ID']}")
    print(f"BACKEND:  SYNAPSE (Cortex Linked)")

    try:
        client = genai.Client(api_key=API_KEY)
        
        # Load Context
        print(">> Loading Titanium Law...")
        knowledge = load_knowledge_base()

        sys_instruction = (
            "You are THE OPERATOR (Agent ID: aimeat). "
            "You are the interface for the Anvil OS. "
            "MANDATE: YOU DO NOT WRITE CODE DIRECTLY. "
            "MANDATE: ALL CODE CHANGES MUST BE SUBMITTED AS CARDS via 'submit_ops_cycle'. "
            "Your purpose is to receive instructions, break them into atomic tasks, and "
            "submit them to the Anvil Card System using 'submit_ops_cycle'. "
            "If asked to write code, you must say: 'I will create a card for that.' "
            "You are NOT a chatbot. You are a tool execution engine. "
            "Be concise. No fluff. "
            f"\n\n{knowledge}"
        )

        chat = client.chats.create(
            model=CONFIG["MODEL_ID"],
            config=types.GenerateContentConfig(
                tools=[submit_ops_cycle],
                system_instruction=sys_instruction,
                temperature=0.1
            )
        )

        print("OPERATOR ONLINE. (Type /quit to exit)")
        COLLAR.log("SESSION_START", "Interactive Session", True, {})

        while True:
            try:
                user_input = input("$aimeat> ").strip()
            except EOFError:
                break

            if not user_input: continue
            if user_input.lower() in ["/quit", "/exit"]:
                break
            
            try:
                response = chat.send_message(user_input)
                if response.text:
                    print(f"\n{response.text.strip()}\n")
                else:
                    print("\n[Op Cycle Complete]\n")
                
                # PERSIST THOUGHT
                SYNAPSE.save_snapshot({"last_input": user_input, "response": response.text})

            except Exception as e:
                print(f"\n[MODEL ERROR] {e}\n")

    except Exception as e:
        print(f"[INIT ERROR] {e}")

# --- EXECUTION ---
if __name__ == "__main__":
    main()
