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
from rich.syntax import Syntax

# --- CONFIGURATION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
DB_PATH = os.path.join(PROJECT_ROOT, "runtime", "cortex.db")
STREAM_FILE = os.path.join(PROJECT_ROOT, "ext", "ladysmith_stream.txt")

# --- DATA FETCHING ---

def get_queue_stats():
    stats = {"PENDING": 0, "PROCESSING": 0, "FAILED": 0, "COMPLETE": 0}
    recent_jobs = []
    try:
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT status, COUNT(*) as count FROM jobs GROUP BY status")
            for row in cursor.fetchall():
                s = row["status"].upper()
                if s in stats: stats[s] = row["count"]
                elif s == "NEEDS_CODING": stats["PENDING"] += row["count"]
                elif s == "ASSIGNED": stats["PROCESSING"] += row["count"]
            cursor.execute("SELECT correlation_id, status, created_at, priority FROM jobs ORDER BY updated_at DESC LIMIT 8")
            recent_jobs = [dict(row) for row in cursor.fetchall()]
            conn.close()
    except: pass
    return stats, recent_jobs

def read_stream():
    if not os.path.exists(STREAM_FILE): return "Waiting for neural link..."
    try:
        with open(STREAM_FILE, "r") as f:
            lines = f.readlines()
            return "".join(lines[-30:]) # Show last 30 lines
    except: return "Stream Error"

# --- UI COMPONENTS ---

def make_layout():
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=10)
    )
    layout["main"].split_row(
        Layout(name="stats", ratio=1),
        Layout(name="stream", ratio=2)
    )
    return layout

def update_header():
    grid = Table.grid(expand=True)
    grid.add_column(justify="left", ratio=1)
    grid.add_column(justify="right")
    grid.add_row(
        "[b cyan]ANVIL OS[/b cyan] | [b white]SYSTEM OVERWATCH[/b white]",
        datetime.now().strftime("%H:%M:%S")
    )
    return Panel(grid, style="white on black")

def update_stats(stats):
    table = Table.grid(expand=True)
    table.add_row(Panel(Align.center(f"[bold cyan]{stats['PENDING']}[/]", vertical="middle"), title="QUEUE", border_style="cyan"))
    table.add_row(Panel(Align.center(f"[bold yellow]{stats['PROCESSING']}[/]", vertical="middle"), title="RUNNING", border_style="yellow"))
    table.add_row(Panel(Align.center(f"[bold green]{stats['COMPLETE']}[/]", vertical="middle"), title="FINISHED", border_style="green"))
    table.add_row(Panel(Align.center(f"[bold red]{stats['FAILED']}[/]", vertical="middle"), title="FAILED", border_style="red"))
    return table

def update_stream():
    content = read_stream()
    # Attempt to detect if it's JSON/Python or just text
    lexer = "json" if "{" in content else "python"
    renderable = Syntax(content, lexer, theme="monokai", line_numbers=False, word_wrap=True)
    return Panel(renderable, title="[b green]LADYSMITH NEURAL STREAM[/b green]", border_style="green")

def update_footer(jobs):
    table = Table(expand=True, box=box.SIMPLE_HEAD, border_style="bright_black")
    table.add_column("ID", style="dim cyan")
    table.add_column("Prio", justify="center")
    table.add_column("Status")
    table.add_column("Created")
    
    styles = {"PENDING": "cyan", "PROCESSING": "bold yellow", "COMPLETE": "green", "FAILED": "bold red", "NEEDS_CODING": "magenta"}
    for j in jobs:
        s = j.get("status", "???").upper()
        table.add_row(j.get("correlation_id", "")[:12], str(j.get("priority", 0)), Text(s, style=styles.get(s, "white")), j.get("created_at", ""))
    return Panel(table, title="Recent Activity", border_style="blue")

def main():
    console = Console()
    layout = make_layout()
    
    with Live(layout, screen=True, refresh_per_second=4) as live:
        try:
            while True:
                stats, jobs = get_queue_stats()
                layout["header"].update(update_header())
                layout["stats"].update(update_stats(stats))
                layout["stream"].update(update_stream())
                layout["footer"].update(update_footer(jobs))
                time.sleep(0.2)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
