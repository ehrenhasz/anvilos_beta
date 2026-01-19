#!/usr/bin/env python3
import time
import sqlite3
import json
import subprocess
import os
import sys
import select # For non-blocking input
from collections import deque
from datetime import datetime

# VISUALS
import rich
import rich.live
import rich.layout
import rich.panel
import rich.table
import rich.align
import rich.text
import rich.box
import shutil

# METRICS
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# --- CONFIGURATION ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(PROJECT_ROOT, "runtime", "hydrogen.db")
LOG_FILE = os.path.join(PROJECT_ROOT, "ext", "forge.log")
SERVICE_NAME = "bigiron"

# --- THEME: "ACID BURN" (90s Cyber-Goth) ---
C_PRIMARY = "#50fa7b"   # Neon Green (Matrix)
C_SECONDARY = "#ff79c6" # Hot Pink (Burn)
C_ACCENT = "#bd93f9"    # Electric Purple
C_WARN = "#f1fa8c"      # Warning Yellow
C_ERR = "#ff5555"       # Error Red
C_LABEL = "#6272a4"     # Muted Blue/Grey
C_BORDER = "#44475a"    # Dark Grey
C_TEXT = "#f8f8f2"      # Off-white

# --- NETWORK STATE MONITOR ---
class NetMonitor:
    def __init__(self):
        self.last_sent = 0
        self.last_recv = 0
        self.last_time = time.time()
        self.up_speed = 0.0
        self.down_speed = 0.0
        
        if HAS_PSUTIL:
            try:
                net = psutil.net_io_counters()
                self.last_sent = net.bytes_sent
                self.last_recv = net.bytes_recv
            except: pass

    def update(self):
        if not HAS_PSUTIL: return
        
        now = time.time()
        try:
            net = psutil.net_io_counters()
            delta_time = now - self.last_time
            if delta_time >= 1.0:
                # Calculate Speed (Bytes -> MB per second)
                self.up_speed = (net.bytes_sent - self.last_sent) / 1024 / 1024 / delta_time
                self.down_speed = (net.bytes_recv - self.last_recv) / 1024 / 1024 / delta_time
                
                # Reset
                self.last_sent = net.bytes_sent
                self.last_recv = net.bytes_recv
                self.last_time = now
        except: pass

net_mon = NetMonitor()

# --- HELPER: DISK USAGE ---
def get_disk_str(path):
    if not os.path.exists(path):
        return "[dim]--[/]"
    try:
        usage = shutil.disk_usage(path)
        used_gb = usage.used / (1024**3)
        total_gb = usage.total / (1024**3)
        pct = (usage.used / usage.total) * 100
        
        # ASCII Bar
        bar_len = 5
        fill = int((pct / 100) * bar_len)
        bar = f"[{C_SECONDARY}]" + "▊" * fill + f"[{C_BORDER}]" + "▊" * (bar_len - fill)
        
        return f"{bar} {used_gb:.0f}/{total_gb:.0f}G"
    except: return "[red]ERR[/]"

# --- LAYOUT & PANELS ---
def make_layout():
    root = rich.layout.Layout(name="root")
    root.split(
        rich.layout.Layout(name="header", size=1),
        rich.layout.Layout(name="cards", ratio=2), 
        rich.layout.Layout(name="btop", ratio=1),
        rich.layout.Layout(name="footer", size=1),
    )
    root["btop"].split_row(
        rich.layout.Layout(name="left", ratio=1),
        rich.layout.Layout(name="right", ratio=2),
    )
    root["left"].split(
        rich.layout.Layout(name="cpu_mem", ratio=1),
        rich.layout.Layout(name="net", size=6),
    )
    root["right"].split(
        rich.layout.Layout(name="proc", ratio=1), 
    )
    return root

class Header:
    def __rich__(self):
        t = rich.text.Text()
        t.append(" [!] ANVIL_OS ", style="bold #000000 on #ff79c6") # Hot Pink Background
        t.append(f" v3.0 // BIG_IRON ", style="bold white on #44475a")
        t.append(" >> ACTIVE ", style="bold #50fa7b")
        t.append(" " * 5)
        t.append(datetime.now().strftime("%H:%M:%S"), style="bold white")
        return rich.align.Align.center(t)

class Footer:
    def __rich__(self):
        t = rich.text.Text()
        t.append(" c ", style="reverse #ff79c6")
        t.append(" CLS (Purge Done) ", style=C_TEXT)
        t.append(" q ", style="reverse #ff5555")
        t.append("QUIT ", style=C_TEXT)
        t.append(" " * 5)
        t.append(" <-> CRASH_OVERRIDE ", style=C_ACCENT)
        return rich.align.Align.center(t)

def system_monitor_panel():
    table = rich.table.Table(box=None, padding=(0, 0), expand=True)
    table.add_column("RSC", style=C_LABEL, width=8)
    table.add_column("VAL", style=C_TEXT)
    
    # 1. CPU / MEM
    if HAS_PSUTIL:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        
        c_cpu = C_PRIMARY if cpu < 50 else C_SECONDARY if cpu < 80 else C_ERR
        table.add_row("CPU", f"[{c_cpu}]{cpu:>4.0f}%[/]")
        table.add_row("RAM", f"[{C_ACCENT}]{mem.used/(1024**3):.1f}G[/]")
    else:
        table.add_row("SYS", "[red]N/A[/]")

    # 2. DISK (Compact)
    table.add_row("[dim]──[/]", "[dim]─────[/]")
    table.add_row("ROOT", get_disk_str("/"))
    table.add_row("TEMP", get_disk_str("/mnt"))

    # 3. BIG IRON PID
    table.add_row("[dim]──[/]", "[dim]─────[/]")
    found = False
    if HAS_PSUTIL:
        for p in psutil.process_iter(['name', 'cmdline']):
            try:
                if p.info['cmdline'] and 'card_reader.py' in ' '.join(p.info['cmdline']):
                    table.add_row("IRON", f"[{C_PRIMARY}]ON[/]")
                    found = True
                    break
            except: pass
    if not found: table.add_row("IRON", f"[{C_ERR}]OFF[/]")

    return rich.panel.Panel(table, title="[bold #ff79c6]HARDWARE[/]", border_style=C_BORDER, box=rich.box.SQUARE, padding=(0,1))

def net_panel():
    net_mon.update()    
    # Check Service
    try:
        res = subprocess.run(["systemctl", "is-active", SERVICE_NAME], capture_output=True, text=True)
        status = res.stdout.strip().upper()
    except: status = "?"
    
    color = C_PRIMARY if status=='ACTIVE' else C_ERR
    
    table = rich.table.Table.grid(expand=True)
    table.add_row(f"[{C_LABEL}]STATUS:[/]  [{color}]{status}[/]")
    table.add_row(f"[{C_LABEL}]UPLINK:[/]  [{C_SECONDARY}]{net_mon.up_speed:.1f} MB/s[/] ^")
    table.add_row(f"[{C_LABEL}]DOWNLN:[/]  [{C_ACCENT}]{net_mon.down_speed:.1f} MB/s[/] v")
    
    return rich.panel.Panel(table, title="[bold #50fa7b]NET_IO[/]", border_style=C_BORDER, box=rich.box.SQUARE, padding=(0,1))

# --- HYDROGEN READER (With CLS) ---
class HydrogenReader:
    def __init__(self, db_path):
        self.db_path = db_path
        self.stats = {"proc": 0, "queue": 0, "done": 0, "fail": 0}
        self.cards = []

    def purge_completed(self):
        """ The 'CLS' function: Deletes Complete/Failed jobs """
        if not os.path.exists(self.db_path): return
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM jobs WHERE status IN ('COMPLETE', 'FAILED')")
            conn.commit()
            conn.close()
        except: pass

    def scan(self):
        if not os.path.exists(self.db_path): return
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Stats
            cursor.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
            rows = cursor.fetchall()
            self.stats = {"proc": 0, "queue": 0, "done": 0, "fail": 0}
            for r in rows:
                s = r[0].lower()
                c = r[1]
                if s == "processing": self.stats["proc"] = c
                elif s in ["pending", "paused"]: self.stats["queue"] += c
                elif s == "complete": self.stats["done"] = c
                elif s == "failed": self.stats["fail"] = c

            # Feed
            cursor.execute("""
                SELECT correlation_id, priority, cost_center, status, payload 
                FROM jobs 
                ORDER BY 
                    CASE status 
                        WHEN 'PROCESSING' THEN 1 
                        WHEN 'FAILED' THEN 2 
                        WHEN 'COMPLETE' THEN 3 
                        ELSE 4 
                    END ASC,
                    updated_at DESC 
                LIMIT 18
            """,)
            self.cards = [dict(row) for row in cursor.fetchall()]
            conn.close()
        except: pass

def cards_panel(reader):
    table = rich.table.Table(expand=True, box=None, padding=(0, 1), show_header=True, header_style=f"bold {C_SECONDARY}")
    table.add_column("PR", width=2, justify="center")
    table.add_column("ID", style=C_LABEL, width=8)
    table.add_column("TAG", style=C_ACCENT, width=4)
    table.add_column("STATE", width=10)
    table.add_column("PAYLOAD")

    for c in reader.cards:
        cid = c['correlation_id'][:8]
        status = c['status'].upper()
        prio = c['priority']
        cost = c['cost_center'][:3].upper() if c['cost_center'] else "GEN"
        
        # Payload Preview
        desc = "..."
        try:
            if isinstance(c['payload'], str): data = json.loads(c['payload'])
            else: data = c['payload']
            desc = data.get('details') or data.get('instruction') or data.get('description') or "DATA"
            desc = str(desc).replace("\n", " ")
        except: desc = "ERR"
        if len(desc) > 50: desc = desc[:47] + "..."

        # 90s Icons & Styles
        if status == "COMPLETE": 
            s_icon = "[green]DONE[/]"
            desc = f"[dim]{desc}[/dim]"
        elif status == "FAILED": 
            s_icon = "[red bold]FAIL[/]"
            desc = f"[red]{desc}[/red]"
        elif status == "PROCESSING": 
            s_icon = "[yellow bold]RUN [/]"
            desc = f"[yellow]{desc}[/yellow]"
        else: # PENDING
            s_icon = "[dim]WAIT[/]"
        
        # Priority ASCII Icons
        if prio >= 90: p_icon = "!!"
        elif prio >= 50: p_icon = "++"
        else: p_icon = "--"

        table.add_row(p_icon, cid, cost, s_icon, desc)

    # Status Bar
    sub = f"[{C_WARN}]RUN:{reader.stats['proc']}[/]   [{C_SECONDARY}]QUE:{reader.stats['queue']}[/]   [{C_PRIMARY}]OK :{reader.stats['done']}[/]   [{C_ERR}]ERR:{reader.stats['fail']}[/]"
    
    return rich.panel.Panel(table, title="[bold #bd93f9]HYDROGEN_FEED[/]", subtitle=sub, border_style=C_BORDER, box=rich.box.SQUARE, padding=(0,1))

# --- LOG TAILER ---
class LogTailer:
    def __init__(self, log_path, max_lines=15):
        self.log_path = log_path
        self.max_lines = max_lines
        self.lines = deque(maxlen=max_lines)

    def update(self):
        if not os.path.exists(self.log_path):
            self.lines.append("[dim]Waiting for logs...[/]")
            return
            
        try:
            with open(self.log_path, 'r') as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                f.seek(max(0, size - 8192)) # Read last 8KB
                raw_lines = f.read().splitlines()
                
                self.lines.clear()
                for line in raw_lines[-self.max_lines:]:
                    try:
                        # Try parsing as MicroJSON (RFC-0002)
                        data = json.loads(line)
                        event_id = data.get("@ID", 0)
                        msg = data.get("data", str(data))
                        ts = data.get("ts", "")
                        if ts: ts = ts.split("T")[-1][:8] # Just time
                        
                        style = C_TEXT
                        if event_id == 1: style = f"bold {C_PRIMARY}" # SYSTEM
                        elif event_id == 2: style = C_PRIMARY # SUCCESS
                        elif event_id == 3: style = C_ERR     # FAILURE
                        elif event_id == 4: style = C_WARN    # WARNING
                        elif event_id == 5: style = C_ACCENT  # OPS_STEP
                        
                        self.lines.append(f"[{C_LABEL}]{ts}[/] [{style}]{msg}[/]")
                    except:
                        # Fallback to plain text
                        self.lines.append(line)
        except: pass

    def get_panel(self):
        t = rich.text.Text.from_markup("\n".join(self.lines))
        return rich.panel.Panel(t, title="[bold #6272a4]LOGS[/]", box=rich.box.SQUARE, border_style=C_BORDER)

# --- MAIN LOOP ---
def main():
    root = make_layout()
    reader = HydrogenReader(DB_PATH)
    tailer = LogTailer(LOG_FILE)
    
    # Hide Cursor
    sys.stdout.write("\033[?25l")
    
    with rich.live.Live(root, refresh_per_second=10, screen=True) as live:
        try:
            while True:
                # NON-BLOCKING INPUT (Linux/Mac)
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1)
                    if key.lower() == 'q': break
                    if key.lower() == 'c': reader.purge_completed()
                
                # Updates
                reader.scan()
                tailer.update()
                
                root["header"].update(Header())
                root["footer"].update(Footer())
                root["cards"].update(cards_panel(reader))
                root["cpu_mem"].update(system_monitor_panel())
                root["net"].update(net_panel())
                root["proc"].update(tailer.get_panel())
                
                time.sleep(0.1)
        except KeyboardInterrupt: pass
        finally:
            sys.stdout.write("\033[?25h") # Show Cursor

if __name__ == "__main__":
    main()
