#!/usr/bin/env python3
import time
import json
import subprocess
import os
from datetime import datetime
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich import box

# THEME: LESBIAN CYBERPUNK 90S HACKER
C_PRIMARY = "bold #9D00FF" # Purple
C_SECONDARY = "bold #FF00FF" # Neon Pink
C_ACCENT = "bold #00FF00" # Neon Green
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
        grid.add_column(justify="right")
        grid.add_row(
            Text.from_markup(f"🔮 [white]BIGIRON[/white] // [purple]MONITOR_V1.0[/purple]"),
            Text.from_markup(f"[white]{datetime.now().strftime('%H:%M:%S')}[/white]")
        )
        return Panel(grid, style=f"on {C_BORDER}", box=box.ASCII)

class Footer:
    def __rich__(self) -> Panel:
        return Panel(
            Text.from_markup(f"🧬 [purple]STATUS:[/purple] [green]STABLE[/green] | 🩸 [purple]AUTH:[/purple] [white]bigiron[/white] | ⛓️ [purple]LINK:[/purple] [green]ACTIVE[/green]"),
            style=f"on {C_BORDER}",
            box=box.ASCII
        )

def generate_panel(title, content, color=C_PRIMARY):
    return Panel(
        content,
        title=f"[{color}]{title}[/{color}]",
        border_style=C_BORDER,
        box=box.DOUBLE
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
            status_text = f"[{C_ACCENT}]● ONLINE[/{C_ACCENT}]"
            details = f"[dim]PID: {os.getpid()} (Simulated)[/dim]" # Placeholder for actual PID
        else:
            status_text = f"[bold red]● {status.upper()}[/bold red]"
            details = "[dim]Check system logs[/dim]"

        grid = Table.grid(expand=True)
        grid.add_column()
        grid.add_row(f"SERVICE: {SERVICE_NAME}")
        grid.add_row(f"STATUS:  {status_text}")
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
    
    stats_grid.add_row(f"[{C_TEXT}]PENDING:[/{C_TEXT}]", f"[{C_SECONDARY}]{pending}[/{C_SECONDARY}]")
    stats_grid.add_row(f"[{C_TEXT}]WORKING:[/{C_TEXT}]", f"[{C_ACCENT}]{working}[/{C_ACCENT}]")
    stats_grid.add_row(f"[{C_TEXT}]FAILED :[/{C_TEXT}]", f"[red]{failed}[/red]")
    stats_grid.add_row(f"[{C_TEXT}]DONE   :[/{C_TEXT}]", f"[blue]{complete}[/blue]")
    
    # Build Task Display
    if current_task:
        task_text = Text()
        task_text.append(f"ID: {current_task.get('id', '???')}\n", style=C_SECONDARY)
        task_text.append(f"{current_task.get('description', 'No description')[:100]}...", style="dim white")
    else:
        task_text = Text("No active tasks.", style="dim italic")

    return stats_grid, task_text

def main():
    layout = make_layout()
    
    # Initialize Header/Footer
    layout["header"].update(Header())
    layout["footer"].update(Footer())
    layout["tty_stream"].update(generate_panel("📟 TTY_STREAM", "[dim]Initializing matrix feed...[/dim]", C_PRIMARY))

    with Live(layout, refresh_per_second=2, screen=True) as live:
        try:
            while True:
                # 1. Update Service Health
                layout["service_status"].update(generate_panel("📡 INT30_WARDEN", get_service_health(), C_SECONDARY))
                
                # 2. Update Queue Stats & Current Task
                stats, task_info = get_queue_data()
                layout["queue_stats"].update(generate_panel("📊 QUEUE_METRICS", stats, C_ACCENT))
                layout["current_task"].update(generate_panel("⚒️ ACTIVE_CARD", task_info, C_PRIMARY))
                
                # 3. Update Header Time
                layout["header"].update(Header())
                
                time.sleep(1)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
