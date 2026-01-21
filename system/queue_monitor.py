#!/usr/bin/env python3
import time
import sqlite3
import os
from datetime import datetime
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.align import Align
from rich import box
from rich.text import Text

# --- CONFIGURATION ---
# Path relative to this script: ../runtime/cortex.db
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
DB_PATH = os.path.join(PROJECT_ROOT, "runtime", "cortex.db")

# --- DATABASE ---
def get_queue_stats():
    """Queries the cortex.db for job status counts."""
    stats = {
        "PENDING": 0,   # Queue
        "PROCESSING": 0, # Running
        "FAILED": 0,
        "COMPLETE": 0
    }
    
    recent_jobs = []

    try:
        if not os.path.exists(DB_PATH):
            return stats, [("System", "DB Not Found", "CRITICAL")]

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get Counts
        cursor.execute("SELECT status, COUNT(*) as count FROM jobs GROUP BY status")
        rows = cursor.fetchall()
        for row in rows:
            status = row["status"].upper()
            # Map various statuses to our core 4 if needed, or just trust the DB
            if status in stats:
                stats[status] = row["count"]
            else:
                # Handle unexpected statuses by mapping them loosely or adding them
                if status == "NEEDS_CODING": stats["PENDING"] += row["count"]
                elif status == "ASSIGNED": stats["PROCESSING"] += row["count"]
                
        # Get Recent Activity (Last 10)
        cursor.execute("""
            SELECT correlation_id, status, created_at, priority 
            FROM jobs 
            ORDER BY updated_at DESC LIMIT 10
        """)
        recent_jobs = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
    except Exception as e:
        recent_jobs.append({"correlation_id": "ERR", "status": "DB_ERROR", "created_at": str(e)})
        
    return stats, recent_jobs

# --- UI COMPONENTS ---

def make_header():
    grid = Table.grid(expand=True)
    grid.add_column(justify="left", ratio=1)
    grid.add_column(justify="right")
    grid.add_row(
        "[b white]CORTEX QUEUE MONITOR[/b white]",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    return Panel(grid, style="white on black", box=box.SIMPLE)

def make_stat_panel(title, count, color):
    return Panel(
        Align.center(f"[bold {color} text]{count}[/]", vertical="middle"),
        title=f"[{color}]{title}[/]",
        border_style=color,
        box=box.ROUNDED,
        height=5
    )

def make_dashboard(stats, jobs):
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="stats", size=7),
        Layout(name="list")
    )

    layout["header"].update(make_header())

    # Stat Row
    layout["stats"].split_row(
        Layout(make_stat_panel("QUEUE", stats["PENDING"], "cyan")),
        Layout(make_stat_panel("RUNNING", stats["PROCESSING"], "yellow")),
        Layout(make_stat_panel("COMPLETED", stats["COMPLETE"], "green")),
        Layout(make_stat_panel("FAILED", stats["FAILED"], "red")),
    )

    # Job List
    table = Table(title="Recent Activity", expand=True, box=box.SIMPLE_HEAD, border_style="bright_black")
    table.add_column("ID", style="dim cyan", width=12)
    table.add_column("Priority", justify="center", width=8)
    table.add_column("Status", width=12)
    table.add_column("Timestamp", justify="right", style="dim white")

    status_styles = {
        "PENDING": "cyan",
        "PROCESSING": "bold yellow reverse",
        "COMPLETE": "green",
        "FAILED": "bold red",
        "NEEDS_CODING": "magenta"
    }

    for job in jobs:
        s = job.get("status", "UNKNOWN").upper()
        style = status_styles.get(s, "white")
        
        table.add_row(
            job.get("correlation_id", "???")[:8],
            str(job.get("priority", 0)),
            Text(s, style=style),
            job.get("created_at", "")
        )

    layout["list"].update(Panel(table, title="Active Stream", border_style="blue"))
    
    return layout

# --- MAIN LOOP ---
def main():
    console = Console()
    console.clear()
    
    with Live(console=console, screen=True, refresh_per_second=2) as live:
        try:
            while True:
                stats, jobs = get_queue_stats()
                live.update(make_dashboard(stats, jobs))
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
