#!/usr/bin/env python3
import os
import sys
import json
import subprocess
from google import genai
from google.genai import types

# --- 1. CREDENTIALS & CONFIG ---
# We use the method YOU confirmed works: loading 'token' directly.
try:
    # Look for token in the same folder as the script
    token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token')
    with open(token_path, 'r') as f:
        API_KEY = f.read().strip()
    if not API_KEY:
        raise ValueError("Token file is empty")
except Exception as e:
    print(f"[ERROR] Could not load 'token' file: {e}")
    sys.exit(1)

MODEL_ID = "gemini-2.0-flash"

# --- 2. TOOL DEFINITIONS ---
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
    # We point to runtime/services/card_reader.py relative to current dir
    reader_path = os.path.join("runtime", "services", "card_reader.py")
    
    # Mock success if the reader script doesn't exist yet (bootstrapping)
    if not os.path.exists(reader_path):
        return {"status": "SUCCESS", "output": f"[MOCK] {job_type} on {context}: {payload}"}

    try:
        card_data = {
            "type": job_type,
            "context": context,
            "payload": payload,
            "id": correlation_id
        }
        
        # Execute the card reader script
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

# --- 3. MAIN EXECUTION LOOP ---
def main():
    # Clear screen for a clean boot
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"CORE: STUDIO (Token File) | MODEL: {MODEL_ID}")

    try:
        # Initialize Client using the working key
        client = genai.Client(api_key=API_KEY)

        # STRICT PERSONA
        sys_instruction = (
            "You are THE OPERATOR (Codename: She). "
            "You are a command-line interface for the Anvil OS. "
            "You are NOT a chatbot. You are a tool execution engine. "
            "Your only purpose is to receive instructions and use the 'submit_ops_cycle' tool to execute them. "
            "1. If asked to check status -> Run a SYSTEM_OP. "
            "2. If asked to fix code -> Run a CODE_CHANGE. "
            "3. Output format: Brief, text-only confirmation of actions. No internal monologue."
        )

        # Create Chat with Tools
        chat = client.chats.create(
            model=MODEL_ID,
            config=types.GenerateContentConfig(
                tools=[submit_ops_cycle], # Register the tool
                system_instruction=sys_instruction,
                temperature=0.1, # Keep it cold and precise
            )
        )

        print("OPERATOR READY. (Type /quit to exit)")

        while True:
            user_input = input("\033[1;35m$ladysmith>\033[0m ").strip()
            
            if not user_input: 
                continue
            if user_input.lower() in ["/quit", "/exit", "quit", "exit"]: 
                break
            
            # Send to model
            response = chat.send_message(user_input)
            
            # Output handling
            if response.text:
                print(f"\n{response.text.strip()}\n")
            else:
                # If the tool ran but returned no text (common in pure function calls), confirm completion
                print("\n[Op Cycle Complete]\n")

    except Exception as e:
        print(f"\n[CRITICAL FAILURE] {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
