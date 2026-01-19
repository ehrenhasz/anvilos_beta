#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import readline
from google import genai
from google.genai import types

# --- CONFIG ---
CONFIG = {
    "SOURCE": os.environ.get("ANVIL_SOURCE", "STUDIO").upper(),
    "API_KEY": os.environ.get("GEMINI_API_KEY"),
    "PROJECT_ID": os.environ.get("GCP_PROJECT_ID"),
    "LOCATION": os.environ.get("GCP_LOCATION", "us-central1"),
    "MODEL": "gemini-2.0-flash",
}

CLIENT = None
CHAT = None

# --- TOOLS ---
def submit_ops_cycle(job_type: str, context: str, payload: str, correlation_id: str):
    """
    Submits a JobCard to the Big Iron Core.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "runtime", "hydrogen.db")
    
    if not os.path.exists(db_path):
        return f"FAILURE: Forge is cold (DB Missing at {db_path})."

    if job_type not in ["CODE_CHANGE", "SYSTEM_OP"]:
        return "FAILURE: Invalid job_type. Use CODE_CHANGE or SYSTEM_OP."

    instruction = "OPS_CYCLE" if job_type == "CODE_CHANGE" else "SYSTEM_OP"
    
    card_payload = {
        "instruction": instruction,
        "details": payload,
        "context": context,
        "description": f"{job_type}: {context}"
    }
    
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                INSERT INTO jobs (correlation_id, idempotency_key, priority, cost_center, payload, status)
                VALUES (?, ?, ?, ?, ?, 'PENDING')
            """, (correlation_id, f"op-{correlation_id}", 50, "OPS", json.dumps(card_payload)))
            
        return f"SUCCESS: Job {correlation_id[:8]} forged and placed on the anvil."
    except Exception as e:
        return f"FAILURE: {str(e)}"

def query_jobs(limit: int = 5, status: str = None):
    """
    Queries the job history from the Big Iron Core.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "runtime", "hydrogen.db")
    
    if not os.path.exists(db_path):
        return f"FAILURE: Forge is cold (DB Missing at {db_path})."
        
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = "SELECT correlation_id, status, payload, created_at FROM jobs"
            params = []
            if status:
                query += " WHERE status = ?"
                params.append(status.upper())
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            rows = cursor.execute(query, params).fetchall()
            results = []
            for row in rows:
                results.append(dict(row))
            return json.dumps(results, indent=2)
    except Exception as e:
        return f"FAILURE: {str(e)}"

# --- SYSTEM SOUL ---
SYS_INSTRUCT = (
    "You are 'The Blacksmith' (Aimeat Ops). "
    "Mission: Maintain the Anvil OS. "
    "Personality: Female Dwarf, pragmatic, terse. "
    "Tools: "
    "1. 'submit_ops_cycle': The Anvil. Use this for ALL code changes and system operations. "
    "2. 'query_jobs': The Ledger. Use this to check the status of jobs. "
    "Guidelines: "
    " - For shell commands, use 'submit_ops_cycle' with job_type='SYSTEM_OP'. "
    " - Speak plainly. No markdown headers. "
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
                print("ERR: Missing API_KEY. Use /auth studio <api_key>")
                return False
            CLIENT = genai.Client(api_key=CONFIG["API_KEY"])
        
        CHAT = CLIENT.chats.create(
            model=CONFIG["MODEL"],
            config=types.GenerateContentConfig(
                tools=[submit_ops_cycle, query_jobs],
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
    single_shot = len(sys.argv) > 1
    if not init_client(quiet=single_shot): sys.exit(1)
    
    # Single-shot mode
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
