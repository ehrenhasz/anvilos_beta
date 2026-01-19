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

# THEME: BTOP (CYBERPUNK VARIANT)
C_PRIMARY = "bold #bd93f9"   # Dracula Purple
C_SECONDARY = "bold #ff79c6" # Dracula Pink
C_ACCENT = "bold #50fa7b"    # Dracula Green
C_WARN = "bold #ffb86c"      # Dracula Orange
C_ERR = "bold #ff5555"       # Dracula Red
C_BORDER = "#6272a4"         # Muted Blue/Grey
C_TEXT = "#f8f8f2"           # Off White
C_LABEL = "#6272a4"          # Dim Grey for labels

QUEUE_FILE = "runtime/card_queue.json"
SERVICE_NAME = "titanium_warden"

console = Console()

def make_layout() -> Layout:
    layout = Layout(name="root")
    
    # btop style: usually one cohesive grid, but we keep the header/footer rail
    layout.split(
        Layout(name="header", size=1), # Minimal top bar
        Layout(name="main", ratio=1),
        Layout(name="footer", size=1), # Minimal bottom bar
    )
    
    layout["main"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=2), # Give more space to the stream/task
    )
    
    layout["left"].split(
        Layout(name="service_status", size=10),
        Layout(name="queue_stats", ratio=1),
    )
    
    layout["right"].split(
        Layout(name="current_task", size=10),
        Layout(name="tty_stream", ratio=1),
    )
    
    return layout

class Header:
    def __rich__(self) -> Text:
        # btop header is often just a text bar with info scattered
        time_str = datetime.now().strftime('%H:%M:%S')
        
        # Construct a wide bar
        # [ BIGIRON v1.0 ] ---------------- [ cpu: 4% ] [ mem: 12% ] ---------------- [ time ]
        
        text = Text()
        text.append(" 🔮 BIGIRON ", style=f"reverse {C_PRIMARY}")
        text.append(" CONSTRUCT_V1 ", style=f"bold white on {C_BORDER}")
        text.append(" " * 4)
        text.append("monitoring: ", style=C_LABEL)
        text.append(SERVICE_NAME, style=C_ACCENT)
        
        # Filler
        text.append(" " * 10) # Dynamic padding would be better but simple for now
        
        text.append(f"{time_str}", style=f"{C_TEXT} on {C_BORDER}")
        return Align.center(text)

class Footer:
    def __rich__(self) -> Text:
        # btop footer keys
        text = Text()
        text.append(" 1 ", style=f"reverse {C_LABEL}")
        text.append(" HELP ", style=f"black on {C_LABEL}")
        text.append(" 2 ", style=f"reverse {C_LABEL}")
        text.append(" OPTIONS ", style=f"black on {C_LABEL}")
        text.append(" Q ", style=f"reverse {C_ERR}")
        text.append(" QUIT ", style=f"black on {C_ERR}")
        
        text.append(" " * 4)
        text.append("INTEGRITY: ", style=C_LABEL)
        text.append("STABLE ", style=C_ACCENT)
        text.append("AUTH: ", style=C_LABEL)
        text.append("OMEGA", style=C_SECONDARY)
        
        return Align.center(text)

def generate_panel(title, content, color=C_PRIMARY):
    return Panel(
        content,
        title=f"[{color} bold]{title}[/]",
        title_align="left",
        border_style=C_BORDER,
        box=box.ROUNDED, # The btop signature
        padding=(0, 1)
    )

def get_service_health():
    """Checks systemd service status."""
    try:
        # Check active state
        result = subprocess.run(
            ["systemctl", "is-active", SERVICE_NAME], 
            capture_output=True, 
            text=True
        )
        status = result.stdout.strip()
        
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="right", ratio=1)
        
        if status == "active":
            status_text = f"[{C_ACCENT}]active[/]"
            graph = f"[{C_ACCENT}]■■■■■■■■■■[/]"
        else:
            status_text = f"[{C_ERR}]{status}[/]"
            graph = f"[{C_ERR}]■■■.......[/]"

        grid.add_row(f"[{C_LABEL}]status[/]", status_text)
        grid.add_row(f"[{C_LABEL}]pid[/]", f"[{C_TEXT}]{os.getpid()}[/]")
        grid.add_row(f"[{C_LABEL}]load[/]", graph)
        
        return grid
    except Exception as e:
        return Text(f"Err: {str(e)}", style="red")

def get_queue_data():
    """Parses the card queue for stats and active task."""
    pending = 0
    working = 0
    failed = 0
    complete = 0
    current_task = None
    
    try:
        with open(QUEUE_FILE, 'r') as f:
            cards = json.load(f)
            
        for card in cards:
            s = card.get('status', 'pending').lower()
            if s == 'pending': pending += 1
            elif s == 'review' or s == 'in_progress': working += 1
            elif s == 'failed': failed += 1
            elif s == 'complete': complete += 1
            
            if not current_task and (s == 'review' or s == 'in_progress' or s == 'pending'):
                current_task = card
    except:
        pass
        
    # btop style stats: Label ............ Value
    stats_grid = Table.grid(expand=True)
    stats_grid.add_column(justify="left")
    stats_grid.add_column(justify="right")
    
    def add_stat(label, value, color):
        stats_grid.add_row(
            f"[{C_LABEL}]{label}[/]", 
            f"[{color}]{value}[/]"
        )

    add_stat("pending", pending, C_SECONDARY)
    add_stat("working", working, C_ACCENT)
    add_stat("failed", failed, C_ERR)
    add_stat("archived", complete, C_BORDER) # Dimmer for archived
    
    # Task Info
    if current_task:
        task_text = Text()
        task_text.append(f"{current_task.get('id', '???')}", style=C_SECONDARY)
        task_text.append(" :: ", style=C_LABEL)
        task_text.append(f"{current_task.get('status', '???').upper()}\n", style=C_ACCENT)
        
        desc = current_task.get('description', 'No description')
        if len(desc) > 80: desc = desc[:80] + "..."
        task_text.append(desc, style=C_TEXT)
    else:
        task_text = Text("IDLE", style=f"italic {C_LABEL}")

    return stats_grid, task_text

class FileWatcher:
    def __init__(self, buffer_size=20):
        self.buffer = deque(maxlen=buffer_size)
        self.last_files = {} 
        self.first_run = True

    def scan(self):
        try:
            cmd = [
                "find", ".", 
                "-type", "f", 
                "-not", "-path", "*/.*", 
                "-not", "-path", "*/node_modules/*", 
                "-not", "-path", "*/__pycache__/*",
                "-printf", "%T@ %p %s\\n"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            current_files = {}
            events = []

            for line in lines:
                if not line: continue
                parts = line.split(' ', 2)
                if len(parts) < 3: continue
                
                mtime = float(parts[0])
                path = parts[1]
                
                current_files[path] = mtime

                if path in self.last_files:
                    if mtime > self.last_files[path]:
                        events.append((mtime, f"MODIFIED {path}"))
                elif not self.first_run:
                     if time.time() - mtime < 10:
                         events.append((mtime, f"CREATED  {path}"))

            self.last_files = current_files
            self.first_run = False
            
            events.sort(key=lambda x: x[0])
            for _, msg in events:
                self.buffer.append(msg)
                
        except Exception:
             pass

    def get_renderable(self):
        text = Text()
        for line in self.buffer:
            if "MODIFIED" in line:
                # btop log style: timestamp (implied) - msg
                text.append("M ", style=C_WARN)
                text.append(line.replace("MODIFIED ", "") + "\n", style=C_TEXT)
            elif "CREATED" in line:
                text.append("C ", style=C_ACCENT)
                text.append(line.replace("CREATED  ", "") + "\n", style=C_TEXT)
            else:
                text.append(f"  {line}\n", style=C_LABEL)
        return text

def main():
    layout = make_layout()
    watcher = FileWatcher()
    
    with Live(layout, refresh_per_second=4, screen=True) as live:
        try:
            while True:
                layout["header"].update(Header())
                layout["footer"].update(Footer())
                
                layout["service_status"].update(generate_panel("system", get_service_health(), C_PRIMARY))
                
                stats, task_info = get_queue_data()
                layout["queue_stats"].update(generate_panel("queue", stats, C_SECONDARY))
                layout["current_task"].update(generate_panel("task", task_info, C_WARN))
                
                watcher.scan()
                layout["tty_stream"].update(generate_panel("stream", watcher.get_renderable(), C_BORDER))
                
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
