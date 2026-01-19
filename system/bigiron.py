#!/usr/bin/env python3
import time
import json
import subprocess
import os
from collections import deque
from datetime import datetime
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich import box
from rich.align import Align
from rich.progress import BarColumn, Progress, TextColumn

# BTOP FIDELITY THEME
C_PRIMARY = "bold #bd93f9"   # Purple
C_SECONDARY = "bold #ff79c6" # Pink
C_ACCENT = "bold #50fa7b"    # Green
C_WARN = "bold #f1fa8c"      # Yellow
C_ERR = "bold #ff5555"       # Red
C_BORDER = "#44475a"         # Muted Dracula
C_LABEL = "#6272a4"          # Comment Grey
C_TEXT = "#f8f8f2"           # Foreground

QUEUE_FILE = "runtime/card_queue.json"
SERVICE_NAME = "titanium_warden"

def make_layout() -> Layout:
    layout = Layout(name="root")
    layout.split(
        Layout(name="header", size=1),
        Layout(name="cards", ratio=1),  # UPPER HALF (Card Reader)
        Layout(name="btop", ratio=1),   # LOWER HALF (Btop Modules)
        Layout(name="footer", size=1),
    )
    
    # Btop Lower Half Layout
    layout["btop"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=2),
    )
    layout["left"].split(
        Layout(name="cpu", ratio=1),
        Layout(name="mem", ratio=1),
        Layout(name="net", size=8),
    )
    layout["right"].split(
        Layout(name="proc", ratio=1), 
    )
    return layout

# ... (Header/Footer remain same)

def cards_panel():
    # Simple Dir List style
    table = Table(expand=True, box=None, padding=(0, 1), show_header=True, header_style=C_LABEL)
    table.add_column("ID", style=C_ACCENT, width=12)
    table.add_column("STATUS", style=C_LABEL, width=12)
    table.add_column("DESCRIPTION", style=C_TEXT)
    
    try:
        with open(QUEUE_FILE, "r") as f:
            cards = json.load(f)
            # Show pending/active first
            cards.sort(key=lambda x: x.get('status') == 'complete')
            
            for c in cards:
                s = c.get("status", "???")
                desc = c.get("description", "").replace("\n", " ")
                
                status_style = C_LABEL
                if s == "complete": status_style = f"dim {C_BORDER}"
                elif s == "failed": status_style = C_ERR
                elif s == "pending": status_style = C_SECONDARY
                elif s in ["review", "in_progress"]: status_style = f"reverse {C_WARN}"
                
                row_style = "dim" if s == "complete" else ""
                
                table.add_row(
                    c.get("id", "???"), 
                    Text(s.upper(), style=status_style), 
                    desc,
                    style=row_style
                )
    except: 
        table.add_row("ERROR", "READING", "QUEUE")

    return Panel(table, title="[bold #bd93f9]card_reader[/]", border_style=C_BORDER, box=box.ROUNDED)

# ... (Standard Panels remain same, simplified update loop)

def main():
    layout = make_layout()
    watcher = FileWatcher()
    with Live(layout, refresh_per_second=4, screen=True) as live:
        try:
            while True:
                watcher.scan()
                layout["header"].update(Header())
                layout["footer"].update(Footer())
                
                # Card Reader (Top)
                layout["cards"].update(cards_panel())
                
                # Btop (Bottom)
                layout["cpu"].update(cpu_panel())
                layout["mem"].update(mem_panel())
                layout["net"].update(net_panel())
                layout["proc"].update(proc_panel(watcher))
                
                time.sleep(0.25)
        except KeyboardInterrupt: pass

if __name__ == "__main__":
    main()
