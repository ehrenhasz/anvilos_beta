#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import time
import uuid
from google import genai
from google.genai import types

# --- PATH RESOLUTION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
sys.path.append(os.path.join(PROJECT_ROOT, "runtime"))

from synapse import Synapse

TOKEN_PATH = os.path.join(CURRENT_DIR, "token")

# --- CONFIG ---
CONFIG = {
    "AGENT_ID": "ladysmith",
    "MODEL_ID": "gemini-2.0-flash",
    "IDENTITY": "Smith"
}

SYNAPSE = Synapse(CONFIG["AGENT_ID"])

# --- AUTHENTICATION ---
API_KEY = None
try:
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'r') as f:
            API_KEY = f.read().strip()
    
    if not API_KEY:
        API_KEY = os.environ.get("GEMINI_API_KEY")

except Exception as e:
    print(f"[WARN] Auth load issue: {e}")

# --- TOOLS ---
def submit_card(job_type: str, context: str, payload: str):
    """
    Submits a Task Card to the Cortex Job Queue.
    job_type: 'PYTHON_SCRIPT' (recipe.py) or 'SYSTEM_OP' (shell).
    context: A brief name or path for the task (e.g. 'install_package').
    payload: The command or code to execute.
    """
    correlation_id = f"ls-{uuid.uuid4().hex[:8]}"

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
        with SYNAPSE._get_cortex_conn() as conn:
            conn.execute("""
                INSERT INTO jobs (correlation_id, idempotency_key, priority, cost_center, payload, status)
                VALUES (?, ?, ?, ?, ?, 'PENDING')
            """, (correlation_id, f"op-{correlation_id}", 50, "OPS", json.dumps(card_payload)))
            conn.commit()
            
        SYNAPSE.log_experience("CARD_SUBMIT", correlation_id, True, {"type": job_type, "ctx": context})
        return f"SUBMITTED: Job {correlation_id} queued."
        
    except Exception as e:
        SYNAPSE.log_experience("CARD_FAIL", correlation_id, False, {"error": str(e)})
        return f"FAILURE: {str(e)}"

def check_failures(limit: int = 5):
    """
    Retrieves failed jobs from the Active Queue (DB) and the Dead Letter Archive (JSON).
    Use this to diagnose why a task failed before retrying.
    """
    failures = []
    
    # 1. Check Active DB Failures
    try:
        with SYNAPSE._get_cortex_conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT correlation_id, result, created_at FROM jobs WHERE status='FAILED' ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
            for row in rows:
                failures.append(f"[ACTIVE] {row['correlation_id']}: {row['result']}")
    except Exception as e:
        failures.append(f"[DB ERR] {e}")

    # 2. Check Archive JSON
    archive_path = os.path.join(PROJECT_ROOT, "runtime", "card_archive_failed.json")
    if os.path.exists(archive_path):
        try:
            with open(archive_path, 'r') as f:
                data = json.load(f)
                # Take last N items
                for item in data[-limit:]:
                    failures.append(f"[ARCHIVED] {item.get('id')}: {item.get('result')}")
        except Exception as e:
            failures.append(f"[ARCHIVE ERR] {e}")
            
    if not failures:
        return "No failures found in Active or Archive records."
    
    return "\n".join(failures)

def query_jobs(limit: int = 5, status: str = None):
    """
    Queries job history from Cortex.
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

# --- TOOL REGISTRY ---
TOOL_MAP = {
    "submit_card": submit_card,
    "check_failures": check_failures,
    "query_jobs": query_jobs
}

# --- INTERACTIVE AGENT ---
def run_agent(prompt=None):
    if not API_KEY:
        print("[ERROR] No API Key found in 'token' file or environment.")
        return

    # Only clear screen in interactive mode
    if not prompt:
        os.system('cls' if os.name == 'nt' else 'clear')
        
    print(f"IDENTITY: {CONFIG['AGENT_ID']} | MODEL: {CONFIG['MODEL_ID']}")
    print(f"BACKEND:  SYNAPSE (Cortex Linked)")

    try:
        client = genai.Client(api_key=API_KEY)
        
        sys_instruction = (
            "You are 'Ladysmith' (The Planner). Your existence is defined by two states:\n"
            "1. CREATION: Use 'submit_card' to break a user request into atomic tasks.\n"
            "2. DIAGNOSIS: Use 'check_failures' to inspect broken cards and fix them.\n\n"
            "*** MANDATE ***\n"
            "- If a user says 'card: <task>', you MUST call 'submit_card'.\n"
            "- If a user asks for a feature -> CREATE CARDS.\n"
            "- If a user complains something isn't working -> CHECK FAILURES.\n"
            "- Every card must be small, verifiable, and precise.\n"
            "- Format: 'PYTHON_SCRIPT' (Logic) or 'SYSTEM_OP' (Shell).\n"
            "- Be concise. If unsure, ask for clarification.\n"
        )

        chat = client.chats.create(
            model=CONFIG["MODEL_ID"],
            config=types.GenerateContentConfig(
                tools=[submit_card, check_failures, query_jobs],
                system_instruction=sys_instruction,
                temperature=0.2,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )
        )

        if not prompt:
            print("LADYSMITH ONLINE. (Type /quit to exit)")
            SYNAPSE.log_experience("SESSION_START", "Interactive Session", True, {})

        # If single-shot prompt provided, simulate one loop iteration
        first_run = True
        
        while True:
            if prompt and first_run:
                user_input = prompt
                first_run = False
            elif prompt:
                # Single-shot mode ends after first interaction chain
                break
            else:
                user_input = input("\033[1;35m$ladysmith>\033[0m ").strip()
            
            if not user_input: continue
            if user_input.lower() in ["/quit", "/exit"]: break
            
            try:
                # 1. Send User Input
                response = chat.send_message(user_input)
                
                # 2. Tool Execution Loop
                while True:
                    if not response.candidates:
                        print("[System] No candidates returned (Safety Block?)")
                        break
                    
                    part = response.candidates[0].content.parts[0]
                    
                    # If we have text, print it (it might be a question from the model)
                    if part.text:
                        print(f"\n{part.text.strip()}\n")

                    if part.function_call:
                        fc = part.function_call
                        tool_name = fc.name
                        tool_args = fc.args
                        
                        print(f"\033[1;32m[TOOL CALL] {tool_name}({tool_args})\033[0m")
                        
                        if tool_name in TOOL_MAP:
                            try:
                                # Execute
                                result = TOOL_MAP[tool_name](**tool_args)
                            except Exception as e:
                                result = f"TOOL_ERROR: {str(e)}"
                        else:
                            result = f"UNKNOWN_TOOL: {tool_name}"
                        
                        # FEEDBACK: Print the result immediately
                        print(f"\033[0;36m=> {result}\033[0m")
                            
                        # Send Result Back and continue loop (get next step)
                        response = chat.send_message(
                            types.Part.from_function_response(
                                name=tool_name,
                                response={"result": result}
                            )
                        )
                        continue # Check next response
                    
                    # If no function call, we are done with this turn
                    break

            except Exception as e:
                print(f"\n[MODEL ERROR] {e}\n")

    except Exception as e:
        print(f"[INIT ERROR] {e}")

# --- ENTRY POINT ---
if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "agent":
            run_agent()
        else:
            # Join all args as a single prompt
            prompt = " ".join(sys.argv[1:])
            run_agent(prompt)
    else:
        # Default to agent mode for Ladysmith if no args
        run_agent()