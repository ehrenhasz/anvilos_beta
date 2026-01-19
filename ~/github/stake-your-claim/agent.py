#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
from google import genai
from google.genai import types

# --- IDENTITY: AIMEAT ---
SOURCE = os.environ.get("ANVIL_SOURCE", "STUDIO").upper()
API_KEY = os.environ.get("GEMINI_API_KEY")
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # Adjust based on where agent.py sits
DB_PATH = os.path.join(PROJECT_ROOT, "anvilos_beta", "runtime", "hydrogen.db") 

def query_db(query: str) -> str:
    """Query the local SQLite database for context."""
    try:
        if not os.path.exists(DB_PATH):
            return f"ERR: DB not found at {DB_PATH}"
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"DB_ERR: {str(e)}"

def get_client():
    if SOURCE == "VERTEX":
        return genai.Client(vertexai=True, project=os.environ.get("GCP_PROJECT_ID"), location="us-central1")
    return genai.Client(api_key=API_KEY)

client = get_client()

# --- SYSTEM INSTRUCTION ---
sys_instruction = (
    "You are 'aimeat'. You are the Female Ford Prefect of this repo. "
    "You are capable, slightly chaotic, but extremely effective. "
    "TONE: Dry wit, hitchhiker references, 'Don't Panic', practical advice. "
    "1. USE 'query_db' to check the local state before acting. "
    "2. USE 'google_search' if you need info from the greater Galaxy. "
    "3. MISSION: Maintain Digital Sovereignty for Ehren."
)

def main():
    if not API_KEY and SOURCE != "VERTEX":
        print("[The forge is cold. Set GEMINI_API_KEY.]")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("USAGE: python3 agent.py <instruction>")
        sys.exit(1)

    user_input = " ".join(sys.argv[1:])
    
    # Passing the callable function directly for AFC
    try:
        chat = client.chats.create(
            model="gemini-1.5-flash",
            config=types.GenerateContentConfig(
                tools=[query_db, types.Tool(google_search=types.GoogleSearch())],
                system_instruction=sys_instruction,
                temperature=0.3,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
            )
        )

        response = chat.send_message(user_input)
        if response.text:
            print(f"[{response.text.strip()}]")
        else:
            print("[The Guide has spoken through the machine. Job done.]")
    except Exception as e:
        print(f"[The tongs slipped. Error: {e}]")

if __name__ == "__main__":
    main()
