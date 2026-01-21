import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "cortex.db")

def init_db():
    print(f"Initializing Cortex DB at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    
    # Jobs Table (The Queue)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            correlation_id TEXT PRIMARY KEY,
            idempotency_key TEXT,
            priority INTEGER,
            cost_center TEXT,
            payload TEXT,
            status TEXT,
            result TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            worker TEXT
        )
    """)
    
    # Agents Table (The Registry)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            agent_id TEXT PRIMARY KEY,
            status TEXT,
            updated_at DATETIME,
            coding_id TEXT
        )
    """)
    
    # Active Plans (Persistence)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS active_plans (
            agent_id TEXT PRIMARY KEY,
            plan_name TEXT,
            content TEXT,
            current_step INTEGER,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Cognitive Snapshots (Memory)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cognitive_snapshots (
            agent_id TEXT PRIMARY KEY,
            memory_dump TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("Cortex Schema Verified.")

if __name__ == "__main__":
    init_db()
