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
        Layout(name="main", ratio=1),
        Layout(name="footer", size=1),
    )
    layout["main"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=2),
    )
    layout["left"].split(
        Layout(name="cpu", ratio=1),
        Layout(name="mem", ratio=1),
        Layout(name="net", size=8),
    )
    layout["right"].split(
        Layout(name="proc", ratio=3), # Matrix Stream / Processes
        Layout(name="task", ratio=1), # Active Card
    )
    return layout

def make_graph(value, color):
    # btop style simple bar
    width = 20
    filled = int((value / 100) * width)
    return f"[{color}]" + "█" * filled + "[/]" + "[#282a36]" + "█" * (width - filled) + "[/]"

class Header:
    def __rich__(self) -> Text:
        t = Text()
        t.append(" BTOP ", style="reverse bold #bd93f9")
        t.append(f" v1.0.0  ")
        t.append(" hostname: ", style=C_LABEL)
        t.append("anvilos-beta  ")
        t.append(" uptime: ", style=C_LABEL)
        t.append("00:42:12  ")
        t.append(" cpu: ", style=C_LABEL)
        t.append("4% ", style=C_ACCENT)
        t.append(" mem: ", style=C_LABEL)
        t.append("12% ", style=C_ACCENT)
        t.append(" " * 20)
        t.append(datetime.now().strftime("%H:%M:%S"), style="bold white")
        return Align.center(t)

class Footer:
    def __rich__(self) -> Text:
        t = Text()
        t.append(" f1 ", style="reverse")
        t.append(" help  ")
        t.append(" f2 ", style="reverse")
        t.append(" options  ")
        t.append(" q ", style="reverse #ff5555")
        t.append(" quit  ")
        t.append(" " * 10)
        t.append(" bigiron_auth: ", style=C_LABEL)
        t.append("OMEGA_SECURE", style=C_SECONDARY)
        return Align.center(t)

def cpu_panel():
    table = Table.grid(expand=True)
    table.add_row(f"[{C_LABEL}]CPU usage[/]", Align.right(f"[{C_ACCENT}]4.2%[/]"))
    table.add_row(make_graph(4.2, C_ACCENT))
    table.add_row("")
    table.add_row(f"[{C_LABEL}]Core 0 [4.1%][/]", make_graph(4.1, C_PRIMARY))
    table.add_row(f"[{C_LABEL}]Core 1 [4.3%][/]", make_graph(4.3, C_PRIMARY))
    return Panel(table, title="[bold #bd93f9]cpu[/]", border_style=C_BORDER, box=box.ROUNDED)

def mem_panel():
    table = Table.grid(expand=True)
    table.add_row(f"[{C_LABEL}]Total:[/]", Align.right(f"[{C_TEXT}]16.0 GB[/]"))
    table.add_row(f"[{C_LABEL}]Used: [/]", Align.right(f"[{C_SECONDARY}]2.4 GB[/]"))
    table.add_row(make_graph(15, C_SECONDARY))
    table.add_row("")
    table.add_row(f"[{C_LABEL}]Swap: [/]", Align.right(f"[{C_LABEL}]0.0 GB[/]"))
    table.add_row(make_graph(0, C_LABEL))
    return Panel(table, title="[bold #ff79c6]mem[/]", border_style=C_BORDER, box=box.ROUNDED)

def net_panel():
    # systemctl integration here
    try:
        res = subprocess.run(["systemctl", "is-active", SERVICE_NAME], capture_output=True, text=True)
        status = res.stdout.strip()
    except: status = "unknown"
    
    table = Table.grid(expand=True)
    table.add_row(f"[{C_LABEL}]service:[/]", f" {SERVICE_NAME}")
    table.add_row(f"[{C_LABEL}]status: [/]", f" [{C_ACCENT if status=='active' else C_ERR}]{status}[/]")
    table.add_row(f"[{C_LABEL}]uplink: [/]", f" [{C_ACCENT}]stable[/]")
    return Panel(table, title="[bold #50fa7b]net[/]", border_style=C_BORDER, box=box.ROUNDED)

def proc_panel(watcher):
    table = Table(expand=True, box=None, padding=(0, 1))
    table.add_column("T", style=C_LABEL, width=1)
    table.add_column("EVENT", style=C_TEXT)
    table.add_column("PATH", style=C_PRIMARY)
    
    for line in list(watcher.buffer)[-15:]: # Show last 15
        if "MODIFIED" in line:
            table.add_row("M", "MODIFIED", line.replace("MODIFIED ", ""), style=C_WARN)
        elif "INJECTED" in line:
            table.add_row("I", "INJECTED", line.replace("INJECTED ", ""), style=C_ACCENT)
        else:
            table.add_row(">", "EVENT", line, style=C_LABEL)
            
    return Panel(table, title="[bold #f1fa8c]proc[/]", border_style=C_BORDER, box=box.ROUNDED)

def task_panel():
    pending = 0; working = 0; failed = 0; done = 0; current = None
    try:
        with open(QUEUE_FILE, "r") as f:
            cards = json.load(f)
            for c in cards:
                s = c.get("status", "").lower()
                if s == "pending": pending += 1
                elif s in ["review", "in_progress"]: working += 1
                elif s == "failed": failed += 1
                elif s == "complete": done += 1
                if not current and s in ["review", "pending", "in_progress"]: current = c
    except: pass

    grid = Table.grid(expand=True)
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    grid.add_row(f"[{C_LABEL}]pending:[/] {pending}", f"[{C_LABEL}]done:[/] {done}")
    grid.add_row(f"[{C_LABEL}]working:[/] {working}", f"[{C_LABEL}]fail:[/] {failed}")
    grid.add_row("")
    if current:
        grid.add_row(Text(f"ACTIVE: {current.get('id')}", style=C_SECONDARY))
        grid.add_row(Text(current.get('description', '')[:100], style="dim"))
    
    return Panel(grid, title="[bold #8be9fd]tasks[/]", border_style=C_BORDER, box=box.ROUNDED)

class FileWatcher:
    def __init__(self, buffer_size=20):
        self.buffer = deque(maxlen=buffer_size)
        self.last_files = {} 
        self.first_run = True

    def scan(self):
        try:
            cmd = ["find", ".", "-type", "f", "-not", "-path", "*/.*", "-not", "-path", "*/node_modules/*", "-printf", "%T@ %p\n"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            current_files = {}
            for line in res.stdout.strip().split("\n"):
                if not line: continue
                mtime, path = line.split(" ", 1)
                mtime = float(mtime)
                current_files[path] = mtime
                if path in self.last_files:
                    if mtime > self.last_files[path]:
                        self.buffer.append(f"MODIFIED {path}")
                elif not self.first_run and (time.time() - mtime < 5):
                    self.buffer.append(f"INJECTED {path}")
            self.last_files = current_files
            self.first_run = False
        except: pass

def main():
    layout = make_layout()
    watcher = FileWatcher()
    with Live(layout, refresh_per_second=4, screen=True) as live:
        try:
            while True:
                watcher.scan()
                layout["header"].update(Header())
                layout["footer"].update(Footer())
                layout["cpu"].update(cpu_panel())
                layout["mem"].update(mem_panel())
                layout["net"].update(net_panel())
                layout["proc"].update(proc_panel(watcher))
                layout["task"].update(task_panel())
                time.sleep(0.25)
        except KeyboardInterrupt: pass

if __name__ == "__main__":
    main()
