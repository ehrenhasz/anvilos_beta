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

# THEME: LESBIAN CYBERPUNK 90S HACKER
C_PRIMARY = "bold #9D00FF" # Deep Purple
C_SECONDARY = "bold #FF0080" # Hot Pink
C_ACCENT = "bold #00FF00" # Hacker Green
C_WARN = "bold #FF5F00" # Safety Orange
C_BORDER = "#4B0082" # Indigo
C_TEXT = "white"

QUEUE_FILE = "runtime/card_queue.json"
SERVICE_NAME = "titanium_warden"

console = Console()

def make_layout() -> Layout:
    layout = Layout(name="root")
    
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3),
    )
    
    layout["main"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=1),
    )
    
    layout["left"].split(
        Layout(name="service_status", ratio=1),
        Layout(name="queue_stats", ratio=1),
    )
    
    layout["right"].split(
        Layout(name="current_task", size=8),
        Layout(name="tty_stream", ratio=1),
    )
    
    return layout

class Header:
    def __rich__(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right", ratio=1)
        
        # Cyberpunk ASCII / Text
        title = Text.from_markup(f"🔮 [{C_PRIMARY}]BIG[/][{C_SECONDARY}]IRON[/] // [{C_ACCENT}]CONSTRUCT_V1[/]")
        sub = Text.from_markup(f"[{C_BORDER}]OPERATOR: bigiron[/]")
        time_str = Text.from_markup(f"[{C_SECONDARY}]TIME:[/{C_SECONDARY}] [{C_TEXT}]{datetime.now().strftime('%H:%M:%S')}[/{C_TEXT}]")
        
        grid.add_row(title, sub, time_str)
        return Panel(grid, style=f"on #1a001a", border_style=C_SECONDARY, box=box.HEAVY)

class Footer:
    def __rich__(self) -> Panel:
        # Integrity Bar
        bar = "█" * 20
        status_line = Text.from_markup(f"🧬 [{C_PRIMARY}]INTEGRITY:[/][{C_ACCENT}]{bar}[/] | 🩸 [{C_PRIMARY}]AUTH:[/][{C_TEXT}] OMEGA[/] | ⛓️ [{C_PRIMARY}]UPLINK:[/][{C_SECONDARY}] SECURE[/]")
        return Panel(
            Align.center(status_line),
            style=f"on #1a001a",
            border_style=C_SECONDARY,
            box=box.HEAVY
        )

def generate_panel(title, content, color=C_PRIMARY):
    return Panel(
        content,
        title=f"[{color}]{title}[/{color}]",
        border_style=color,
        box=box.HEAVY, # Chunky 90s look
        style="on #0d001a" # Very dark purple bg
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
        
        if status == "active":
            status_text = f"[{C_ACCENT}]● SYSTEM_ONLINE[/{C_ACCENT}]"
            details = f"[{C_TEXT}]PID: {os.getpid()} (EMULATED)[/{C_TEXT}]"
        else:
            status_text = f"[bold red]● {status.upper()}[/bold red]"
            details = "[dim]CHECK_SYSTEM_LOGS[/dim]"

        grid = Table.grid(expand=True)
        grid.add_column()
        grid.add_row(f"[{C_SECONDARY}]TARGET :[/{C_SECONDARY}] {SERVICE_NAME}")
        grid.add_row(f"[{C_SECONDARY}]STATUS :[/{C_SECONDARY}] {status_text}")
        grid.add_row(details)
        
        return grid
    except FileNotFoundError:
        return Text("Systemctl not found (Non-Linux?)", style="red")
    except Exception as e:
        return Text(f"Error: {str(e)}", style="red")

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
            
            # Identify current task (first one that is pending or in progress)
            if not current_task and (s == 'review' or s == 'in_progress' or s == 'pending'):
                current_task = card
                
    except Exception:
        pass # Fail gracefully
        
    # Build Stats Grid
    stats_grid = Table.grid(expand=True)
    stats_grid.add_column(justify="left")
    stats_grid.add_column(justify="right")
    
    stats_grid.add_row(f"[{C_TEXT}]PENDING :[/{C_TEXT}]", f"[{C_SECONDARY}]{pending}[/{C_SECONDARY}]")
    stats_grid.add_row(f"[{C_TEXT}]WORKING :[/{C_TEXT}]", f"[{C_ACCENT}]{working}[/{C_ACCENT}]")
    stats_grid.add_row(f"[{C_TEXT}]FAILED  :[/{C_TEXT}]", f"[red]{failed}[/red]")
    stats_grid.add_row(f"[{C_TEXT}]ARCHIVED:[/{C_TEXT}]", f"[blue]{complete}[/blue]")
    
    # Build Task Display
    if current_task:
        task_text = Text()
        task_text.append(f"🆔 {current_task.get('id', '???')}\n", style=C_SECONDARY)
        task_text.append(f"{current_task.get('description', 'No description')[:100]}...", style="white")
    else:
        task_text = Text("💤 SYSTEM_IDLE", style="dim italic")

    return stats_grid, task_text

class FileWatcher:
    def __init__(self, buffer_size=15):
        self.buffer = deque(maxlen=buffer_size)
        self.last_files = {} # path -> mtime
        self.first_run = True

    def scan(self):
        try:
            # Find modified files (excluding hidden and common junk)
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
                size = parts[2]
                
                current_files[path] = mtime

                # Check if new or updated
                if path in self.last_files:
                    if mtime > self.last_files[path]:
                        events.append((mtime, f"MODIFIED -> {path}"))
                elif not self.first_run:
                     if time.time() - mtime < 10:
                         events.append((mtime, f"INJECTED -> {path}"))

            self.last_files = current_files
            self.first_run = False
            
            # Sort events by time and add to buffer
            events.sort(key=lambda x: x[0])
            for _, msg in events:
                self.buffer.append(msg)
                
        except Exception as e:
             self.buffer.append(f"[red]SCAN_ERROR: {e}[/red]")

    def get_renderable(self):
        text = Text()
        for line in self.buffer:
            # Colorize key words
            if "MODIFIED" in line:
                text.append("⚡ ", style=C_WARN)
                text.append(line + "\n", style=C_TEXT)
            elif "INJECTED" in line:
                text.append("✨ ", style=C_ACCENT)
                text.append(line + "\n", style=C_SECONDARY)
            else:
                text.append(f"> {line}\n", style="dim purple")
        return text

def main():
    layout = make_layout()
    watcher = FileWatcher()
    
    # Initialize Header/Footer
    layout["header"].update(Header())
    layout["footer"].update(Footer())

    with Live(layout, refresh_per_second=4, screen=True) as live:
        try:
            while True:
                # 1. Update Service Health
                layout["service_status"].update(generate_panel("📡 WARDEN_LINK", get_service_health(), C_SECONDARY))
                
                # 2. Update Queue Stats & Current Task
                stats, task_info = get_queue_data()
                layout["queue_stats"].update(generate_panel("📊 QUEUE_DATA", stats, C_ACCENT))
                layout["current_task"].update(generate_panel("⚒️ CURRENT_OP", task_info, C_PRIMARY))
                
                # 3. Update Matrix Stream
                watcher.scan()
                layout["tty_stream"].update(generate_panel("📟 MATRIX_FEED", watcher.get_renderable(), C_PRIMARY))
                
                # 4. Update Header Time
                layout["header"].update(Header())
                
                time.sleep(0.5) # Faster refresh for that cyberpunk feel
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
