#!/usr/bin/env python3
import time
import os
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.layout import Layout

# --- CONFIGURATION ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
STREAM_FILE = os.path.join(PROJECT_ROOT, "ext", "ladysmith_stream.txt")

def read_stream():
    if not os.path.exists(STREAM_FILE):
        return "Waiting for stream signal..."
    
    try:
        with open(STREAM_FILE, "r") as f:
            return f.read()
    except Exception as e:
        return f"Stream Error: {e}"

def main():
    console = Console()
    console.clear()
    
    # Initial content
    content = read_stream()
    
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="body")
    )
    
    layout["header"].update(Panel(Text("LADYSMITH NEURAL STREAM", justify="center", style="bold green"), style="green"))
    
    with Live(layout, refresh_per_second=4, screen=True) as live:
        while True:
            new_content = read_stream()
            
            # Syntax highlight as JSON since the output is JSON
            # But the content might be incomplete JSON during streaming, so Syntax might fail or look weird.
            # Plain Text with some coloring might be safer for "raw stream" feel.
            # Or try "python" if it looks like python, but it's wrapped in JSON.
            # Let's stick to a simple green-on-black terminal look for the "stream".
            
            # We scroll to the bottom by taking the last N lines if it's too long, 
            # but Rich Panel handles some overflow.
            
            # Simple heuristic: If it looks like code, highlight it?
            # Let's just use Text with a specific style.
            
            renderable = Syntax(new_content, "json", theme="monokai", line_numbers=True, word_wrap=True)
            
            layout["body"].update(Panel(renderable, title="Live Buffer", border_style="green"))
            
            time.sleep(0.1)

if __name__ == "__main__":
    main()
