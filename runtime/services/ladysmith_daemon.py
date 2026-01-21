#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import time

# --- THE AMNESIA PROTOCOL ---
os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
os.environ.pop("GOOGLE_CLOUD_PROJECT", None)
os.environ.pop("GCLOUD_PROJECT", None)

from google import genai
from google.genai import types

# --- PATH RESOLUTION ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DB_PATH = os.path.join(PROJECT_ROOT, "runtime", "cortex.db")
TOKEN_PATH = os.path.join(PROJECT_ROOT, "agent_ladysmith", "token")

# --- AUTH ---
API_KEY = os.environ.get("GEMINI_API_KEY")
try:
    if not API_KEY and os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'r') as f:
            API_KEY = f.read().strip()
except: pass

if not API_KEY:
    print("[LADYSMITH] FATAL: No API Key.")
    sys.exit(1)

CLIENT = genai.Client(api_key=API_KEY)
MODEL = "gemini-2.0-flash"

# --- DOCTRINE ---
SYS_INSTRUCT = (
    "You are 'Ladysmith', the Headless Coder for Anvil OS. "
    "Your input is a high-level task (e.g., 'Create a hello world script'). "
    "Your output must be the EXECUTABLE PAYLOAD for BigIron (The Executor). "
    "*** MANDATE ***\n"
    "1. ONE CARD = ONE FILE. Do not generate complex multi-file dumps.\n"
    "2. VERIFICATION: Include a '__main__' block or test to verify the code runs.\n"
    "3. FORMAT: You must return a JSON object with 'instruction' and 'details'.\n"
    "   - For Python: {'instruction': 'OPS_CYCLE', 'details': '<python_code>', 'format': 'recipe.py'}\n"
    "   - For Shell: {'instruction': 'SYSTEM_OP', 'details': '<bash_command>', 'format': 'shell'}\n"
    "4. NO HALLUCINATION: Standard libs only.\n"
)

def generate_code(context, description):
    prompt = f"CONTEXT: {context}\nTASK: {description}\nGenerate the payload."
    STREAM_FILE = os.path.join(PROJECT_ROOT, "ext", "ladysmith_stream.txt")
    
    try:
        # Clear/Init stream file
        with open(STREAM_FILE, "w") as f:
            f.write(f"// INITIATING STREAM FOR: {description}\n")

        # Use the specific stream method for the new SDK
        response = CLIENT.models.generate_content_stream(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYS_INSTRUCT,
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        
        full_text = ""
        with open(STREAM_FILE, "a") as f:
            for chunk in response:
                if chunk.text:
                    f.write(chunk.text)
                    f.flush()
                    full_text += chunk.text
                    
        return json.loads(full_text)
    except Exception as e:
        print(f"[LADYSMITH] Generation Error: {e}")
        return None

def process_queue():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Fetch 'NEEDS_CODING'
        cursor.execute("SELECT correlation_id, payload FROM jobs WHERE status = 'NEEDS_CODING' LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            c_id, payload_raw = row
            print(f"[LADYSMITH] Processing {c_id}...")
            
            try:
                data = json.loads(payload_raw)
                ctx = data.get("context", "general")
                desc = data.get("description", "Unknown Task")
                
                # 2. Generate Code
                result_payload = generate_code(ctx, desc)
                
                if result_payload:
                    # 3. Promote to 'PENDING' for BigIron
                    cursor.execute(
                        "UPDATE jobs SET status = 'PENDING', payload = ?, updated_at = CURRENT_TIMESTAMP WHERE correlation_id = ?", 
                        (json.dumps(result_payload), c_id)
                    )
                    conn.commit()
                    print(f"[LADYSMITH] Code generated for {c_id}. Handing off to BigIron.")
                else:
                    print(f"[LADYSMITH] Failed to generate code for {c_id}.")
                    
            except Exception as e:
                print(f"[LADYSMITH] Payload Parse Error: {e}")
        
        conn.close()
    except Exception as e:
        print(f"[LADYSMITH] DB Error: {e}")

if __name__ == "__main__":
    print("[LADYSMITH] Daemon Online. Watching 'NEEDS_CODING'.")
    while True:
        process_queue()
        time.sleep(2)
