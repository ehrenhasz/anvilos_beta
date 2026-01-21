#!/usr/bin/env python3
import os
import sys
import json
import time
import sqlite3

# --- 1. THE AMNESIA PROTOCOL (AUTH WRAPPER) ---
# We clear these BEFORE importing the heavy libraries to prevent
# the SDK from auto-detecting the wrong credentials.
os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
os.environ.pop("GOOGLE_CLOUD_PROJECT", None)
os.environ.pop("GCLOUD_PROJECT", None)

try:
    from google import genai
    from google.genai import types
except ImportError:
    pass

# --- 2. CREDENTIAL LOADING ---
# Priority: 'token' file > Environment Variable
TOKEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token')
LOADED_API_KEY = None

try:
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'r') as f:
            LOADED_API_KEY = f.read().strip()
except Exception as e:
    print(f"[WARN] Token load failed: {e}")

# If file failed, fall back to env (but we already cleared the GCloud ones, so this relies on explicit API Key vars)
if not LOADED_API_KEY:
    LOADED_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

# --- PATH RESOLUTION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
sys.path.append(os.path.join(PROJECT_ROOT, "runtime"))

# --- SYNAPSE CONNECTION ---
# We assume Synapse is available per your instruction
from synapse import Synapse

# --- CONFIG ---
AGENT_ID = "ladysmith"
CONFIG = {
    "SOURCE": os.environ.get("ANVIL_SOURCE", "STUDIO").upper(),
    "API_KEY": LOADED_API_KEY, # Injected here
    "PROJECT_ID": os.environ.get("GCP_PROJECT_ID"),
    "LOCATION": os.environ.get("GCP_LOCATION", "us-central1"),
    "MODEL": "gemini-2.0-flash",
}

CLIENT = None
CHAT = None
SYNAPSE = None

# --- TOOLS (CORTEX CONNECTED) ---
def submit_card(job_type: str, context: str, payload: str, correlation_id: str):
    """
    Submits a Task Card to the Cortex Job Queue via Synapse.
    job_type: 'PYTHON_SCRIPT' (recipe.py) or 'SYSTEM_OP' (shell).
    """
    global SYNAPSE
    
    valid_types = ["PYTHON_SCRIPT", "SYSTEM_OP"]
    if job_type not in valid_types:
        return f"FAILURE: Invalid job_type. Use {valid_types}."

    card_payload = {
        "context": context,
        "details": payload,
        "description": f"{job_type}: {context}",
        "source": "LADYSMITH"
    }

    if job_type == "PYTHON_SCRIPT":
        card_payload["instruction"] = "OPS_CYCLE"
        card_payload["format"] = "recipe.py"
    else: # SYSTEM_OP
        card_payload["instruction"] = "SYSTEM_OP"
        card_payload["format"] = "shell"
    
    try:
        # Utilizing Synapse's existing connection logic
        with SYNAPSE._get_cortex_conn() as conn:
            conn.execute("""
                INSERT INTO jobs (correlation_id, idempotency_key, priority, cost_center, payload, status)
                VALUES (?, ?, ?, ?, ?, 'PENDING')
            """, (correlation_id, f"op-{correlation_id}", 50, "OPS", json.dumps(card_payload)))
            
        SYNAPSE.log_experience("CARD_SUBMIT", f"Submitted {correlation_id}", True, {"type": job_type, "ctx": context})
        return f"SUBMITTED: Job {correlation_id[:8]} queued."
        
    except Exception as e:
        if SYNAPSE:
            SYNAPSE.log_experience("CARD_FAIL", f"Failed {correlation_id}", False, {"error": str(e)})
        return f"FAILURE: {str(e)}"

def query_jobs(limit: int = 5, status: str = None):
    """
    Queries job history from Cortex via Synapse.
    """
    try:
        with SYNAPSE._get_cortex_conn() as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT correlation_id, status, payload, created_at, result FROM jobs"
            params = []
            if status:
                query += " WHERE status = ?"
                params.append(status.upper())
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(query, params).fetchall()
            results = [dict(row) for row in rows]
            return json.dumps(results, indent=2)
    except Exception as e:
        return f"FAILURE: {str(e)}"

# --- SYSTEM SOUL (DOCTRINE) ---
SYS_INSTRUCT = (
    "You are 'Ladysmith', the Task Ingest Agent for Anvil OS. "
    "Role: Break complex software requests into atomic 'Micro-Cards'. "
    "Tools: 'submit_card' and 'query_jobs'. "
    "\n\n"
    "*** ANVIL CODING DOCTRINE (STRICT COMPLIANCE REQUIRED) ***\n"
    "1. THE COBOL AXIOM: Think of these as punch cards. One Card = One Atomic Unit.\n"
    "   - IDEAL: One Card = One File creation.\n"
    "   - IDEAL: One Card = One Function implementation.\n"
    "   - FORBIDDEN: 'Implement Auth System' (Too big. Break it down.)\n"
    "2. STUPID, SMALL, EASY: Complexity is the enemy. If a card looks hard, you failed to split it.\n"
    "3. MICRO-CHUNKING: Do not boil the ocean.\n"
    "   - BAD: 'Port Vim to Anvil'\n"
    "   - GOOD: 'Create empty buffer.py' -> 'Add insert_char function' -> 'Add save function'\n"
    "4. VERIFICATION: Every card must include a test function to verify itself.\n"
    "5. NO HALLUCINATION: Use standard MicroPython/Anvil libs only. No external pip packages.\n"
    "6. FORMAT: Use 'PYTHON_SCRIPT' for logic. Use 'SYSTEM_OP' only for file/shell ops.\n"
    "\n"
    "Your goal is to feed 'Aimeat' (The Smith) small, stupid, easy chunks."
)

# --- SETUP ---
def init_client(quiet=False):
    global CLIENT, CHAT
    if not quiet:
        print(f"Forge Fuel: {CONFIG['SOURCE']}")
    try:
        if CONFIG["SOURCE"] == "VERTEX":
            if not CONFIG["PROJECT_ID"]:
                print("ERR: Missing PROJECT_ID. Use /auth vertex <project_id> <location>")
                return False
            CLIENT = genai.Client(vertexai=True, project=CONFIG["PROJECT_ID"], location=CONFIG["LOCATION"])
        else:
            if not CONFIG["API_KEY"]:
                print("ERR: Missing API_KEY. Check 'token' file or use /auth studio <api_key>")
                return False
            CLIENT = genai.Client(api_key=CONFIG["API_KEY"])
        
        CHAT = CLIENT.chats.create(
            model=CONFIG["MODEL"],
            config=types.GenerateContentConfig(
                tools=[submit_card, query_jobs],
                system_instruction=SYS_INSTRUCT,
                temperature=0.2,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
            )
        )
        return True
    except Exception as e:
        print(f"Ignition Error: {e}")
        return False

def handle_slash(cmd):
    parts = cmd.split()
    command = parts[0].lower()
    
    if command in ["/quit", "/exit"]:
        print("Cooling down...")
        sys.exit(0)
    elif command == "/auth":
        if len(parts) < 2: return
        target = parts[1].upper()
        
        if target == "VERTEX":
            if len(parts) > 2: CONFIG["PROJECT_ID"] = parts[2]
            if len(parts) > 3: CONFIG["LOCATION"] = parts[3]
        elif target == "STUDIO":
            if len(parts) > 2: CONFIG["API_KEY"] = parts[2]

        if target in ["STUDIO", "VERTEX"]:
            CONFIG["SOURCE"] = target
            if init_client():
                safe_config = {k: v for k, v in CONFIG.items() if k != "API_KEY"}
                print(f"\n{json.dumps(safe_config, indent=2)}\n")
    elif command == "/clear":
        os.system('clear')

def main():
    global SYNAPSE
    
    # 1. Boot Synapse
    try:
        SYNAPSE = Synapse(AGENT_ID)
        SYNAPSE.log_experience("BOOT", "Ladysmith v2.1 Online (Auth Wrapped)", True, {})
        print(f"[{AGENT_ID}] ONLINE via Synapse")
    except Exception as e:
        print(f"[CRITICAL] Synapse Boot Failed: {e}")
        sys.exit(1)

    # 2. Check for Single-Shot Args
    single_shot = len(sys.argv) > 1
    
    # 3. Initialize Gemini
    if not init_client(quiet=single_shot): 
        sys.exit(1)
    
    # 4. Single-shot Execution
    if single_shot:
        user_input = " ".join(sys.argv[1:])
        try:
            response = CHAT.send_message(user_input)
            if response.text:
                print(f"{response.text.strip()}")
            else:
                print("*Clang* (Done)")
        except Exception as e:
            print(f"Error: {e}")
        return

    # 5. Interactive Loop
    print("Forge Hot. (Type /quit to exit)")
    
    while True:
        try:
            user_input = input("\033[1;35m$ladysmith>\033[0m ").strip()
            if not user_input: continue
            if user_input.startswith("/"):
                handle_slash(user_input)
                continue
                
            response = CHAT.send_message(user_input)
            if response.text:
                print(f"\n{response.text.strip()}\n")
            else:
                print("\n*Clang* (Done)\n")
                
        except KeyboardInterrupt:
            print("\nCooling down...")
            sys.exit(0)
        except Exception as e:
            print(f"\nError: {e}\n")

if __name__ == "__main__":
    main()
