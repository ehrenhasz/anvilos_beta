#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import readline
import time
try:
    from google import genai
    from google.genai import types
except ImportError:
    pass

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
def submit_card(job_type: str, context: str, payload: str, correlation_id: str):
    """
    Submits a Task Card to the Job Queue and waits briefly for a result.
    job_type: 'PYTHON_SCRIPT' for python code, 'SYSTEM_OP' for shell commands.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "runtime", "hydrogen.db")
    
    if not os.path.exists(db_path):
        return f"FAILURE: DB Missing at {db_path}."

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
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                INSERT INTO jobs (correlation_id, idempotency_key, priority, cost_center, payload, status)
                VALUES (?, ?, ?, ?, ?, 'PENDING')
            """, (correlation_id, f"op-{correlation_id}", 50, "OPS", json.dumps(card_payload)))
            
        # FAST POLL (User requested speed)
        # Wait up to 5 seconds, checking every 0.25s
        start_time = time.time()
        while time.time() - start_time < 5.0:
            time.sleep(0.25)
            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.execute("SELECT status, result FROM jobs WHERE correlation_id=?", (correlation_id,))
                    row = cursor.fetchone()
                    if row:
                        status, result = row
                        if status == "COMPLETE":
                            return f"SUCCESS: {result}"
                        elif status == "FAILED":
                            return f"FAILURE: {result}"
            except: pass
            
        return f"SUBMITTED: Job {correlation_id[:8]} queued (Async)."
        
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
            query = "SELECT correlation_id, status, payload, created_at, result FROM jobs"
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
    "You are 'Ladysmith', the Task Ingest Agent for Anvil OS. "
    "Role: Receive commands -> Create Task Cards -> Submit to Queue. "
    "Tools: 'submit_card' and 'query_jobs'. "
    "Mandates: "
    "1. You do NOT execute tasks. You only file them. "
    "2. Use 'PYTHON_SCRIPT' for python code/recipes. "
    "3. Use 'SYSTEM_OP' for shell commands. "
    "4. If a task FAILS (tool returns FAILURE), analyze the error and Retry with fixed code/logic immediately. "
    "5. Keep responses brief. "
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
