#!/usr/bin/env python3
import time
import json
import subprocess
import os
import sys
import threading
from datetime import datetime
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Console
from rich import box
from rich.align import Align

# --- CONFIGURATION ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
QUEUE_FILE = os.path.join(PROJECT_ROOT, "runtime", "card_queue.json")
LOG_FILE = os.path.join(PROJECT_ROOT, "ext", "forge.log")
SERVICE_NAME = "titanium_warden"

# BTOP DEFAULT FIDELITY THEME
C_PRIMARY = "#50fa7b"   # Green
C_SECONDARY = "#8be9fd" # Cyan
C_ACCENT = "#bd93f9"    # Purple
C_WARN = "#f1fa8c"      # Yellow
C_ERR = "#ff5555"       # Red
C_LABEL = "#6272a4"     # Grey
C_BORDER = "#44475a"    # Muted
C_TEXT = "#f8f8f2"

# --- SYSTEM MONITOR (No dependencies) ---
class SystemMonitor:
    def __init__(self):
        self.last_cpu_time = 0
        self.last_cpu_idle = 0
        self.cpu_usage = 0.0

    def get_cpu_stats(self):
        try:
            with open('/proc/stat', 'r') as f:
                line = f.readline()
                parts = line.split()
                times = [float(x) for x in parts[1:]]
                idle = times[3] + times[4] # idle + iowait
                total = sum(times)
                return total, idle
        except:
            return 0, 0

    def poll_cpu(self):
        total, idle = self.get_cpu_stats()
        diff_total = total - self.last_cpu_time
        diff_idle = idle - self.last_cpu_idle
        
        if diff_total > 0:
            self.cpu_usage = 100.0 * (1.0 - (diff_idle / diff_total))
        
        self.last_cpu_time = total
        self.last_cpu_idle = idle
        return self.cpu_usage

    def get_mem_usage(self):
        try:
            mem_info = {}
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    parts = line.split(':')
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = int(parts[1].split()[0]) # kB
                        mem_info[key] = val
            
            total = mem_info.get('MemTotal', 1)
            avail = mem_info.get('MemAvailable', 0)
            used = total - avail
            percent = (used / total) * 100.0
            return used / 1024 / 1024, total / 1024 / 1024, percent # GB, GB, %
        except:
            return 0, 0, 0

# --- CARDREADER (View Only) ---
class CardReaderView:
    def __init__(self, file_path):
        self.file_path = file_path
        self.cards = []
        self.stats = {"proc": 0, "queue": 0, "done": 0, "fail": 0}
        self.scan()

    def scan(self):
        try:
            if not os.path.exists(self.file_path):
                return
            with open(self.file_path, "r") as f:
                self.cards = json.load(f)
            
            self.stats = {"proc": 0, "queue": 0, "done": 0, "fail": 0}
            for c in self.cards:
                s = c.get("status", "???").lower()
                if s == "processing": self.stats["proc"] += 1
                elif s == "pending": self.stats["queue"] += 1
                elif s == "complete": self.stats["done"] += 1
                elif s == "failed": self.stats["fail"] += 1
        except Exception:
            pass

# --- DASHBOARD TUI ---
monitor = SystemMonitor()
reader = CardReaderView(QUEUE_FILE)

def make_graph(value, color, width=15):
    filled = int((min(max(value, 0), 100) / 100) * width)
    return f"[{color}]" + "█" * filled + "[/]" + f"[{C_BORDER}]" + "█" * (width - filled) + "[/]"

def generate_header():
    t = Text()
    t.append(" ANVIL OS ", style="reverse bold #8be9fd")
    t.append(" Mainframe ", style="bold white")
    t.append(" host: ", style=C_LABEL)
    t.append("anvilos ", style=C_PRIMARY)
    t.append(" " * 5)
    t.append(datetime.now().strftime("%H:%M:%S"), style="bold white")
    return Align.center(t)

def generate_stats():
    cpu = monitor.poll_cpu()
    used_mem, total_mem, mem_pct = monitor.get_mem_usage()
    
    table = Table.grid(expand=True)
    table.add_row(f"[{C_LABEL}]CPU usage[/]", Align.right(f"[{C_PRIMARY}]{cpu:.1f}%[/]"))
    table.add_row(make_graph(cpu, C_PRIMARY, width=25))
    table.add_row("")
    
    mem_style = C_SECONDARY if mem_pct < 60 else C_WARN if mem_pct < 85 else C_ERR
    table.add_row(f"[{C_LABEL}]Mem used[/]", Align.right(f"[{mem_style}]{used_mem:.1f}G[/]"))
    table.add_row(make_graph(mem_pct, mem_style, width=25))
    
    return Panel(table, title="[bold #bd93f9]system[/]", border_style=C_BORDER, box=box.SQUARE)

def generate_net_panel():
    try:
        # Check if service is active
        res = subprocess.run(["systemctl", "is-active", SERVICE_NAME], capture_output=True, text=True)
        status = res.stdout.strip()
    except:
        status = "unknown"
        
    style = C_PRIMARY if status == "active" else C_ERR
    
    table = Table.grid(expand=True)
    table.add_row(f"[{C_LABEL}]warden:[/]  [{style}]{status.upper()}[/]")
    
    return Panel(table, title="[bold #50fa7b]service[/]", border_style=C_BORDER, box=box.SQUARE)

def generate_queue_table():
    reader.scan()
    
    # Text Log View (Dense)
    card_text = Text()
    
    # Sort: Priority (desc), then ID
    sorted_cards = sorted(
        reader.cards, 
        key=lambda c: c.get("priority", 50), 
        reverse=True
    )

    for card in sorted_cards[:15]:
        prio = card.get("priority", 50)
        prio_icon = "🔴" if prio > 80 else "🟢" if prio < 30 else "⚪"
        
        status = card.get("status", "unknown")
        status_style = {
            "pending": f"dim {C_WARN}",
            "processing": "bold #8be9fd", # Cyan
            "complete": C_PRIMARY,
            "failed": f"bold {C_ERR}",
            "paused": "magenta"
        }.get(status, "white")
        
        cost = card.get("cost_center", "gen")[:3].upper()
        desc = card.get("description", "")[:50]
        cid = card.get("id", "?")
        
        # [PRIO] [ID] STATUS (COST) DESC
        card_text.append(f"{prio_icon} ", style="white")
        card_text.append(f"[{cid}] ", style=C_LABEL)
        card_text.append(f"{status.upper():<10} ", style=status_style)
        card_text.append(f"({cost}) ", style=f"dim {C_SECONDARY}")
        card_text.append(f"{desc}\n", style=C_TEXT)
        
    sub = f"[{C_ACCENT}]proc {reader.stats['proc']}[/] | [{C_WARN}]pend {reader.stats['queue']}[/] | [{C_PRIMARY}]done {reader.stats['done']}[/] | [{C_ERR}]fail {reader.stats['fail']}[/]"
        
    return Panel(card_text, title="[bold #bd93f9]card_queue[/]", subtitle=sub, border_style=C_BORDER, box=box.SQUARE)

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )
    layout["body"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=3)
    )
    layout["left"].split_column(
        Layout(name="stats", ratio=1),
        Layout(name="net", size=5)
    )
    
    layout["header"].update(generate_header())
    layout["footer"].update(Align.center(Text("Ctrl+C to Quit | Dashboard Mode (ReadOnly)", style="dim")))
    layout["right"].update(generate_queue_table())
    layout["stats"].update(generate_stats())
    layout["net"].update(generate_net_panel())
    
    return layout

def main():
    console = Console()
    console.clear()
    
    with Live(make_layout(), refresh_per_second=4, screen=True) as live:
        try:
            while True:
                live.update(make_layout())
                time.sleep(0.25)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
