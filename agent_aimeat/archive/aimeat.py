#!/usr/bin/env python3
import os
import sys
import json
import subprocess
from google import genai
from google.genai import types

# --- CONFIGURATION ---
# We prioritize Standard Google Env Vars, fallback to custom ones
CONFIG = {
    "SOURCE": os.environ.get("ANVIL_SOURCE", "VERTEX").upper(), # Default to Vertex for stability
    "PROJECT_ID": os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT_ID"),
    "LOCATION": os.environ.get("GOOGLE_CLOUD_LOCATION") or os.environ.get("GCP_LOCATION", "us-central1"),
    "API_KEY": os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"),
    "MODEL": "gemini-1.5-flash-001"
}

# --- TOOL DEFINITION ---
def submit_ops_cycle(job_type: str, context: str, payload: str, correlation_id: str):
    """
    EXECUTE A SYSTEM OPERATION.
    Use this tool to read files, write code, or run shell commands.
    
    Args:
        job_type: 'CODE_CHANGE' (for file edits) or 'SYSTEM_OP' (for shell commands).
        context: The file path (e.g., 'main.py') or component name.
        payload: The exact code to write or command to run.
        correlation_id: A short tag to track this action (e.g., 'fix_bug_1').
    """
    # Sanity check
    if job_type not in ["CODE_CHANGE", "SYSTEM_OP"]:
        return {"status": "FAILURE", "error": "Invalid job_type. Must be CODE_CHANGE or SYSTEM_OP."}

    # Prepare payload for the internal card reader
    card_data = {
        "type": job_type,
        "context": context,
        "payload": payload,
        "id": correlation_id
    }
    
    # Path to the logic core
    reader_path = os.path.join("runtime", "services", "card_reader.py")
    
    try:
        # execute the card reader script
        result = subprocess.run(
            ["python3", reader_path, json.dumps(card_data)], 
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return {"status": "SUCCESS", "output": result.stdout.strip()}
        else:
            return {"status": "FAILURE", "error": result.stderr.strip()}
    except Exception as e:
        return {"status": "CRITICAL_ERROR", "error": str(e)}

# --- CLIENT SETUP ---
def get_client():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"CORE: {CONFIG['SOURCE']} | PROJ: {CONFIG['PROJECT_ID']}")

    try:
        if CONFIG["SOURCE"] == "VERTEX":
            if not CONFIG["PROJECT_ID"]:
                print("ERR: Missing GOOGLE_CLOUD_PROJECT.")
                return None
            return genai.Client(vertexai=True, project=CONFIG["PROJECT_ID"], location=CONFIG["LOCATION"])
        else:
            if not CONFIG["API_KEY"]:
                print("ERR: Missing GOOGLE_API_KEY.")
                return None
            return genai.Client(api_key=CONFIG["API_KEY"])
    except Exception as e:
        print(f"ERR: Init failed: {e}")
        return None

# --- MAIN LOOP ---
def main():
    client = get_client()
    if not client:
        sys.exit(1)

    # STRICT PERSONA - No ambiguity
    sys_instruction = (
        "You are THE OPERATOR (Codename: She). "
        "You are a command-line interface for the Anvil OS. "
        "You are NOT a chatbot. You are a tool execution engine. "
        "Your only purpose is to receive instructions and use the 'submit_ops_cycle' tool to execute them. "
        "1. If asked to check status -> Run a SYSTEM_OP. "
        "2. If asked to fix code -> Run a CODE_CHANGE. "
        "3. Output format: Brief, text-only confirmation of actions. No internal monologue."
    )

    # Initialize Chat with Tools
    chat = client.chats.create(
        model=CONFIG["MODEL"],
        config=types.GenerateContentConfig(
            tools=[submit_ops_cycle, types.Tool(google_search=types.GoogleSearch())],
            system_instruction=sys_instruction,
            temperature=0.1, # Low temp for precision
        )
    )

    print("OPERATOR READY. (Type /quit to exit)")

    while True:
        try:
            user_input = input("\033[1;35m$ladysmith>\033[0m ").strip()
            if not user_input: continue
            if user_input in ["/quit", "/exit"]: break
            
            # Send to model
            response = chat.send_message(user_input)
            
            if response.text:
                print(f"\n{response.text.strip()}\n")
            else:
                print("\n[Action Complete]\n")

        except Exception as e:
            print(f"\n[ERROR] {e}\n")

if __name__ == "__main__":
    main()
