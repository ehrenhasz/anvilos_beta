#!/usr/bin/env python3
import time
from datetime import datetime
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich import box

# THEME: LESBIAN CYBERPUNK 90S HACKER
# Primary: Purple, Secondary: Neon Pink/Green
C_PRIMARY = "bold #9D00FF" # Purple
C_SECONDARY = "bold #FF00FF" # Neon Pink
C_ACCENT = "bold #00FF00" # Neon Green
C_BORDER = "#4B0082" # Indigo

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
        Layout(name="current_task", size=5),
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

def generate_placeholder(title, content, color=C_PRIMARY):
    return Panel(
        Text.from_markup(content),
        title=f"[{color}]{title}[/{color}]",
        border_style=C_BORDER,
        box=box.DOUBLE
    )

def main():
    layout = make_layout()
    
    # Placeholders for now
    layout["header"].update(Header())
    layout["footer"].update(Footer())
    
    layout["service_status"].update(generate_placeholder("📡 SERVICE_STATUS", "Checking systemctl...", C_SECONDARY))
    layout["queue_stats"].update(generate_placeholder("📊 QUEUE_STATS", "PENDING: 0\nWORKING: 0\nFAILED: 0", C_ACCENT))
    layout["current_task"].update(generate_placeholder("⚒️ WORKING_ON", "[yellow]ID: vis_01_monitor_core[/yellow]\nScaffolding the UI structure...", C_PRIMARY))
    layout["tty_stream"].update(generate_placeholder("📟 TTY_STREAM", "[dim]Awaiting code injection...[/dim]", C_PRIMARY))

    with Live(layout, refresh_per_second=4, screen=True) as live:
        try:
            while True:
                time.sleep(1)
                # Update time in header
                layout["header"].update(Header())
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
