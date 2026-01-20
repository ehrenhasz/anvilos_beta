#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import time
from google import genai
from google.genai import types

# --- PATH RESOLUTION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
sys.path.append(os.path.join(PROJECT_ROOT, "runtime"))

from synapse import Synapse

TOKEN_PATH = os.path.join(CURRENT_DIR, "token")

# --- SOVEREIGN CONFIG ---
CONFIG = {
    "AGENT_ID": "aimeat",
    "IDENTITY": "meat0",
    "MODEL_ID": "gemini-2.0-flash"
}

SYNAPSE = Synapse(CONFIG["AGENT_ID"])

# --- AUTHENTICATION (INJECTED) ---
API_KEY = None
try:
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'r') as f:
            API_KEY = f.read().strip()
    
    if not API_KEY:
        # Fallback to env var if file fails, but file is primary
        API_KEY = os.environ.get("GOOGLE_API_KEY")

except Exception as e:
    print(f"[WARN] Auth load issue: {e}")

# --- DB HELPERS ---
def log_ujson(id_code, data):
    print(json.dumps({"@ID": id_code, "data": data}))

# --- CORE: WORKER FUNCTIONS ---
# --- BEGIN BOOT SEQUENCE (PROTECTED - DO NOT MODIFY) ---
def fast_boot():
    """
    State-First Boot: Pulls identity from Cortex DB, logs to temp, no filesystem crawling.
    """
    boot_log_path = "/mnt/anvil_temp/boot.log"
    os.makedirs(os.path.dirname(boot_log_path), exist_ok=True)
    
    try:
        # Direct DB pull for speed and truth
        import sqlite3
        cortex_db_path = "/var/lib/anvilos/db/cortex.db"
        
        identity = CONFIG["IDENTITY"]
        status = "UNKNOWN"
        
        if os.path.exists(cortex_db_path):
            with sqlite3.connect(cortex_db_path) as conn:
                cursor = conn.cursor()
                # Ensure agents table exists (it might not if fresh)
                cursor.execute("CREATE TABLE IF NOT EXISTS agents (agent_id TEXT PRIMARY KEY, status TEXT, updated_at DATETIME)")
                
                # Register/Update Presence
                cursor.execute("INSERT OR REPLACE INTO agents (agent_id, status, updated_at) VALUES (?, 'ONLINE', CURRENT_TIMESTAMP)", (CONFIG["AGENT_ID"],))
                conn.commit()
                status = "ONLINE"
        
        # MicroJSON Log to File (The Collar)
        boot_data = {
            "@ID": 100,
            "data": {
                "agent": CONFIG["AGENT_ID"],
                "identity": identity,
                "mode": "STATE_FIRST",
                "status": status
            }
        }
        
        with open(boot_log_path, "a") as f:
            f.write(json.dumps(boot_data) + "\n")

        # Standard Output for CLI
        log_ujson(100, boot_data["data"])
        
        return "ONLINE"

    except Exception as e:
        err_data = {"@ID": 500, "data": {"error": str(e)}}
        print(json.dumps(err_data))
        return f"FAILURE: {str(e)}"
# --- END BOOT SEQUENCE ---

def process_jobs():
    try:
        job = SYNAPSE.get_job()
        if not job:
            return "NO_JOBS"
        
        job_id = job["correlation_id"]
        
        try:
            payload = json.loads(job["payload"])
            log_ujson(200, {"job": job_id, "status": "STARTING", "desc": payload.get("description")})
            
            fmt = payload.get("format")
            
            if fmt == "recipe.py":
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                    tmp.write(payload["details"])
                    tmp_path = tmp.name
                
                result = subprocess.run([sys.executable, tmp_path], capture_output=True, text=True)
                os.remove(tmp_path)
            
            elif fmt == "shell":
                cmd = payload["details"]
                # Execute shell command directly
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            else:
                # Fallback / Error
                raise ValueError(f"Unknown format: {fmt}")

            # Process Result
            status = "COMPLETED" if result.returncode == 0 else "FAILED"
            output = result.stdout if result.returncode == 0 else result.stderr

            SYNAPSE.update_job(job_id, status, output)
            SYNAPSE.log_experience("JOB_COMPLETE", job_id, status == "COMPLETED", {"output": output[:100]})
            return f"PROCESSED {job_id}: {status}"
            
        except Exception as e:
            SYNAPSE.update_job(job_id, "FAILED", str(e))
            SYNAPSE.log_experience("JOB_CRASH", job_id, False, {"error": str(e)})
            return f"CRASH {job_id}: {str(e)}"
            
    except Exception as e:
        return f"SYNAPSE_ERROR: {str(e)}"

def poll_for_failures(poll_duration=30, delay=5):
    """Polls the DB for failed jobs for a specific duration."""
    end_time = time.time() + poll_duration
    log_ujson(300, {"status": "START_POLLING", "duration": poll_duration})
    
    while time.time() < end_time:
        try:
            with SYNAPSE._get_cortex_conn() as conn:
                conn.row_factory = sqlite3.Row
                failed = conn.execute("SELECT correlation_id, result FROM jobs WHERE status='FAILED'").fetchall()
                if failed:
                    failures = {row['correlation_id']: row['result'] for row in failed}
                    log_ujson(301, {"status": "FAILURES_FOUND", "count": len(failures)})
                    return f"FOUND FAILURES: {json.dumps(failures)}"
        except Exception as e:
            return f"DB_POLL_ERROR: {str(e)}"
        
        time.sleep(delay)
        
    log_ujson(302, {"status": "POLL_COMPLETE_NONE_FOUND"})
    return "NO_FAILURES"

# --- CORE: AGENT TOOLS ---
def submit_ops_cycle(job_type: str, context: str, payload: str, correlation_id: str):
    """
    EXECUTE A SYSTEM OPERATION.
    Args:
        job_type: 'CODE_CHANGE' or 'SYSTEM_OP'.
        context: file path or component name.
        payload: code or command.
        correlation_id: tracking tag.
    """
    if job_type not in ["CODE_CHANGE", "SYSTEM_OP"]:
        return {"status": "FAILURE", "error": "Invalid job_type."}

    # Use relative path from where script is run
    reader_path = os.path.join(PROJECT_ROOT, "runtime", "services", "card_reader.py")
    
    if not os.path.exists(reader_path):
        return {"status": "SUCCESS", "output": f"[MOCK] {job_type} on {context}: {payload}"}

    try:
        card_data = {"type": job_type, "context": context, "payload": payload, "id": correlation_id}
        result = subprocess.run(["python3", reader_path, json.dumps(card_data)], capture_output=True, text=True)
        SYNAPSE.log_experience("OPS_CYCLE", correlation_id, result.returncode == 0, {"type": job_type, "ctx": context})
        return {"status": "SUCCESS", "output": result.stdout.strip()} if result.returncode == 0 else {"status": "FAILURE", "error": result.stderr.strip()}
    except Exception as e:
        return {"status": "CRITICAL_ERROR", "error": str(e)}

# --- CORE: INTERACTIVE AGENT ---
def run_agent():
    if not API_KEY:
        print("[ERROR] No API Key found in 'token' file.")
        return

    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"IDENTITY: {CONFIG['AGENT_ID']} | MODEL: {CONFIG['MODEL_ID']}")
    print(f"BACKEND:  SYNAPSE (Cortex Linked)")

    try:
        client = genai.Client(api_key=API_KEY)
        
        sys_instruction = (
            "You are THE OPERATOR (Codename: She/Aimeat). "
            "You are the interface for the Anvil OS. "
            "You are NOT a chatbot. You are a tool execution engine. "
            "Your purpose is to receive instructions and use 'submit_ops_cycle' to execute them. "
            "Be concise. No fluff."
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
        
        # Log session start
        SYNAPSE.log_experience("SESSION_START", "Interactive Session", True, {})

        while True:
            user_input = input("\033[1;35m$ladysmith>\033[0m ").strip()
            if not user_input: continue
            if user_input.lower() in ["/quit", "/exit"]: break
            
            try:
                response = chat.send_message(user_input)
                if response.text:
                    print(f"\n{response.text.strip()}\n")
                else:
                    print("\n[Op Cycle Complete]\n")
            except Exception as e:
                print(f"\n[MODEL ERROR] {e}\n")

    except Exception as e:
        print(f"[INIT ERROR] {e}")

# --- ENTRY POINT ---
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "boot":
            print(f"Aimeat: {fast_boot()}")
        elif cmd == "work":
            print(f"Aimeat: {process_jobs()}")
        elif cmd == "agent":
            run_agent()
        else:
            print(f"Unknown command: {cmd}")
    else:
        print("Usage: aimeat.py [boot|work|agent]")
