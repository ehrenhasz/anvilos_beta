import sys
import os
import json
import datetime
import subprocess

# --- CONFIGURATION ---
# RFC-0021: The Black Box.
# We write to a local file that simulates the immutable sink.
BLACKBOX_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'blackbox.jsonl'))

class TheCollar:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self._ensure_blackbox()

    def _ensure_blackbox(self):
        try:
            os.makedirs(os.path.dirname(BLACKBOX_PATH), exist_ok=True)
        except Exception:
            pass # Failsafe

    def _log_microjson(self, id_code, data):
        """
        RFC-0002: MicroJSON Enforcement.
        {"@ID": int, "data": ...}
        """
        payload = {
            "@ID": id_code,
            "ts": datetime.datetime.now().isoformat(),
            "agent": self.agent_id,
            "data": data
        }
        
        try:
            with open(BLACKBOX_PATH, 'a') as f:
                f.write(json.dumps(payload) + "\n")
        except Exception as e:
            # If the Black Box is unreachable, we scream to stderr.
            sys.stderr.write(f"[COLLAR_PANIC] BLACKBOX WRITE FAILURE: {e}\n")

    def log(self, event_type, context, success, data):
        """
        Audit Logging.
        ID 100: Info/Success
        ID 500: Failure/Panic
        """
        code = 100 if success else 500
        
        entry = {
            "event": event_type,
            "ctx": context,
            "success": success,
            "details": data
        }
        
        # We log silently to the box.
        self._log_microjson(code, entry)
        
        # We only print to stdout if it's a critical failure or specifically requested audit.
        if not success:
            print(f"[COLLAR] FAILURE: {event_type} - {context}")

    def sh(self, command, context=""):
        """
        Secure Shell Execution.
        Enforces RFC-0027 (Shells) and RFC-0003 (Titanium).
        """
        # 1. Audit the intent
        self._log_microjson(200, {"action": "EXEC_SHELL", "cmd": command, "ctx": context})

        # 2. THE COLLAR (Enforcement)
        blocked_keywords = ["curl ", "wget ", "ssh ", "nc ", "telnet ", "ping ", "sudo "]
        allowed_executables = ["/bin/bash", "/usr/bin/python3", "git", "ls", "cat", "grep", "find", "mkdir", "rm", "cp", "mv", "touch", "echo", "chmod", "gh", "podman"]
        
        # Check for blocked network tools (The Umbilical mandate)
        for keyword in blocked_keywords:
            if keyword in command:
                self._log_microjson(666, {"violation": "NETWORK_ATTEMPT", "cmd": command})
                raise PermissionError(f"[TITANIUM] VIOLATION: Network tool '{keyword.strip()}' is forbidden. Use The Umbilical.")

        # 3. Execute
        try:
            # We use subprocess.run, ensuring we capture everything.
            res = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                executable='/bin/bash' # RFC-0027 Mandate
            )
            
            success = (res.returncode == 0)
            
            # 4. Audit the result (Truncated if too long to prevent log bloat)
            output_snippet = res.stdout[:500] if success else res.stderr[:500]
            self._log_microjson(201, {
                "action": "EXEC_RESULT", 
                "success": success, 
                "code": res.returncode, 
                "out": output_snippet
            })

            return res

        except Exception as e:
            self._log_microjson(500, {"action": "EXEC_CRASH", "error": str(e)})
            raise e