#!/usr/bin/env python3
import os
import sys
import json
import sqlite3

# --- PATH RESOLUTION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
DB_PATH = os.path.join(PROJECT_ROOT, "runtime", "hydrogen.db")

# --- SOVEREIGN CONFIG ---
CONFIG = {
    "DB_PATH": DB_PATH,
    "AGENT_ID": "aimeat",
    "IDENTITY": "meat0"
}

def log_ujson(id_code, data):
    print(json.dumps({"@ID": id_code, "data": data}))

def fast_boot():
    if not os.path.exists(CONFIG["DB_PATH"]):
        return f"FAILURE: DB Missing at {CONFIG['DB_PATH']}"
    try:
        with sqlite3.connect(CONFIG["DB_PATH"]) as conn:
            conn.execute("INSERT OR IGNORE INTO agents (agent_id, status) VALUES (?, 'OFFLINE')", (CONFIG["AGENT_ID"],))
            conn.execute("UPDATE agents SET status='ONLINE', updated_at=CURRENT_TIMESTAMP WHERE agent_id=?", (CONFIG["AGENT_ID"],))
            jobs = conn.execute("SELECT count(*) FROM jobs WHERE status='PENDING'").fetchone()[0]
        
        log_ujson(100, {
            "agent": CONFIG["AGENT_ID"],
            "identity": CONFIG["IDENTITY"],
            "status": "ONLINE",
            "pending_jobs": jobs
        })
        return "ONLINE"
    except Exception as e:
        return f"FAILURE: {str(e)}"

def process_jobs():
    if not os.path.exists(CONFIG["DB_PATH"]):
        return "FAILURE: DB Missing"
    
    try:
        with sqlite3.connect(CONFIG["DB_PATH"]) as conn:
            conn.row_factory = sqlite3.Row
            # Find a pending job
            cursor = conn.execute("SELECT * FROM jobs WHERE status='PENDING' ORDER BY priority DESC, created_at ASC LIMIT 1")
            job = cursor.fetchone()
            
            if not job:
                return "NO_JOBS"
            
            job_id = job["correlation_id"]
            
            # Lock the job
            conn.execute("UPDATE jobs SET status='RUNNING', worker=?, updated_at=CURRENT_TIMESTAMP WHERE correlation_id=?", (CONFIG["AGENT_ID"], job_id))
            conn.commit()
            
            try:
                payload = json.loads(job["payload"])
                log_ujson(200, {"job": job_id, "status": "STARTING", "desc": payload.get("description")})
                
                # Execute Logic
                if payload.get("format") == "recipe.py":
                    # Write recipe to temp file
                    import tempfile
                    import subprocess
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                        tmp.write(payload["details"])
                        tmp_path = tmp.name
                    
                    # Run it
                    result = subprocess.run([sys.executable, tmp_path], capture_output=True, text=True)
                    os.remove(tmp_path)
                    
                    if result.returncode == 0:
                        status = "COMPLETED"
                        output = result.stdout
                    else:
                        status = "FAILED"
                        output = result.stderr
                else:
                    status = "FAILED"
                    output = "Unknown format"

                # Update Job
                conn.execute("UPDATE jobs SET status=?, result=?, updated_at=CURRENT_TIMESTAMP WHERE correlation_id=?", (status, output, job_id))
                conn.commit()
                
                log_ujson(201, {"job": job_id, "status": status, "output": output})
                return f"PROCESSED {job_id}: {status}"
                
            except Exception as e:
                conn.execute("UPDATE jobs SET status='FAILED', result=?, updated_at=CURRENT_TIMESTAMP WHERE correlation_id=?", (str(e), job_id))
                conn.commit()
                return f"CRASH {job_id}: {str(e)}"
                
    except Exception as e:
        return f"DB_ERROR: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "boot":
            print(f"Aimeat: {fast_boot()}")
        elif cmd == "work":
            print(f"Aimeat: {process_jobs()}")
    else:
        print("Usage: aimeat.py [boot|work]")
