import sqlite3
import os
import json
import time
from datetime import datetime

# --- PATH RESOLUTION ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CORTEX_DB = "/var/lib/anvilos/db/cortex.db"

class Synapse:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.local_db = f"/var/lib/anvilos/db/agent_{agent_id}.db"
        self._init_local_db()

    def _get_local_conn(self):
        return sqlite3.connect(self.local_db)

    def _get_cortex_conn(self):
        return sqlite3.connect(CORTEX_DB)

    def _init_local_db(self):
        with self._get_local_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS local_jobs (
                    id TEXT PRIMARY KEY,
                    status TEXT,
                    payload TEXT,
                    result TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS event_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    context TEXT,
                    success BOOLEAN,
                    details TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    synced BOOLEAN DEFAULT 0
                )
            """)

    def log_experience(self, task_type, context, success, details):
        try:
            with self._get_local_conn() as conn:
                conn.execute("""
                    INSERT INTO event_log (event_type, context, success, details)
                    VALUES (?, ?, ?, ?)
                """, (task_type, context, 1 if success else 0, json.dumps(details)))
            self.sync_to_cortex()
        except Exception as e:
            print(f"[SYNAPSE] Log Error: {e}")

    def sync_to_cortex(self):
        try:
            local_conn = self._get_local_conn()
            local_cursor = local_conn.cursor()
            local_cursor.execute("SELECT id, event_type, context, success, details, timestamp FROM event_log WHERE synced=0")
            logs = local_cursor.fetchall()
            
            if not logs: return

            cortex_conn = self._get_cortex_conn()
            cortex_conn.execute("""
                CREATE TABLE IF NOT EXISTS experience_log (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    event_type TEXT,
                    context TEXT,
                    success BOOLEAN,
                    details TEXT,
                    timestamp DATETIME
                )
            """)

            cortex_conn.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    status TEXT,
                    updated_at DATETIME
                )
            """)
            
            for row in logs:
                log_id, et, ctx, suc, det, ts = row
                global_id = f"{self.agent_id}-{log_id}-{ts}"
                cortex_conn.execute("""
                    INSERT OR IGNORE INTO experience_log (id, agent_id, event_type, context, success, details, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (global_id, self.agent_id, et, ctx, suc, det, ts))
                
                # Update Status in agents table
                cortex_conn.execute("UPDATE agents SET status='ONLINE', updated_at=CURRENT_TIMESTAMP WHERE agent_id=?", (self.agent_id,))
                
                local_conn.execute("UPDATE event_log SET synced=1 WHERE id=?", (log_id,))
            
            cortex_conn.commit()
            local_conn.commit()
        except Exception as e:
            print(f"[SYNAPSE] Sync Failed: {e}")
        finally:
            if 'local_conn' in locals(): local_conn.close()
            if 'cortex_conn' in locals(): cortex_conn.close()

    def get_job(self):
        try:
            cortex = self._get_cortex_conn()
            cortex.row_factory = sqlite3.Row
            # Debug
            # print(f"[SYNAPSE] Checking for jobs for {self.agent_id}...")
            cursor = cortex.execute("SELECT * FROM jobs WHERE status='PENDING' AND (worker IS NULL OR worker=?) ORDER BY priority DESC LIMIT 1", (self.agent_id,))
            job = cursor.fetchone()
            if job:
                print(f"[SYNAPSE] Claiming Job: {job['correlation_id']}")
                cortex.execute("UPDATE jobs SET status='ASSIGNED', worker=? WHERE correlation_id=?", (self.agent_id, job['correlation_id']))
                cortex.commit()
                with self._get_local_conn() as local:
                    local.execute("INSERT OR REPLACE INTO local_jobs (id, status, payload) VALUES (?, 'ASSIGNED', ?)", (job['correlation_id'], job['payload']))
                return dict(job)
            else:
                print("[SYNAPSE] No matching jobs found.")
            return None
        except Exception as e:
            print(f"[SYNAPSE] Job Fetch Error: {e}")
            return None

    def update_job(self, job_id, status, result):
        with self._get_local_conn() as local:
            local.execute("UPDATE local_jobs SET status=?, result=? WHERE id=?", (status, str(result), job_id))
        try:
            with self._get_cortex_conn() as cortex:
                cortex.execute("UPDATE jobs SET status=?, result=?, updated_at=CURRENT_TIMESTAMP WHERE correlation_id=?", (status, str(result), job_id))
        except Exception as e:
            print(f"[SYNAPSE] Cortex Update Error: {e}")
