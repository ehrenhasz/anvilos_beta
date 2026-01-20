#!/usr/bin/env python3
import os
import sys
from google import genai

# 1. Load Key
try:
    token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token')
    with open(token_path, 'r') as f:
        api_key = f.read().strip()
    if not api_key: raise ValueError("File is empty")
except Exception as e:
    print(f"Error loading 'token' file: {e}")
    sys.exit(1)

# 2. Initialize Client (New SDK)
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"Client Init Error: {e}")
    sys.exit(1)

# 3. Main Loop
if __name__ == "__main__":
    model_id = "gemini-2.0-flash"
    print(f"--- AI Studio Connected ({model_id}) ---")
    
    # Create a chat session
    chat = client.chats.create(model=model_id)

    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["quit", "exit"]:
                break
            
            # New SDK syntax for sending messages
            response = chat.send_message(user_input)
            print(f"Agent: {response.text}")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
