#!/usr/bin/env python3
import curses
import time
import os
import sys
import subprocess
from datetime import datetime

# CONFIGURATION
REFRESH_RATE = 0.5  # Seconds
TITLE = "BIG IRON // ANVIL OS MONITOR"
USER = os.environ.get("USER", "UNKNOWN")

def get_cpu_usage():
    try:
        # Simple load average
        load = os.getloadavg()
        return f"LOAD: {load[0]:.2f} {load[1]:.2f} {load[2]:.2f}"
    except:
        return "CPU: N/A"

def get_mem_usage():
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        mem_total = int(lines[0].split()[1])
        mem_free = int(lines[1].split()[1])
        used_percent = ((mem_total - mem_free) / mem_total) * 100
        return f"MEM: {used_percent:.1f}%"
    except:
        return "MEM: N/A"

def get_disk_usage():
    try:
        st = os.statvfs('/')
        free = (st.f_bavail * st.f_frsize) / (1024 * 1024 * 1024)
        total = (st.f_blocks * st.f_frsize) / (1024 * 1024 * 1024)
        return f"DISK: {total-free:.1f}/{total:.1f} GB"
    except:
        return "DISK: N/A"

def get_git_status():
    try:
        branch = subprocess.check_output(["git", "branch", "--show-current"], stderr=subprocess.DEVNULL).decode().strip()
        return f"GIT: {branch}"
    except:
        return "GIT: DETACHED"

def draw_menu(stdscr):
    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN) # Header

    while True:
        # Initialization
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Header
        header_text = f" {TITLE} | USER: {USER} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
        stdscr.attron(curses.color_pair(4))
        stdscr.addstr(0, 0, header_text)
        stdscr.addstr(0, len(header_text), " " * (width - len(header_text) - 1))
        stdscr.attroff(curses.color_pair(4))

        # System Stats
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(2, 2, "SYSTEM METRICS")
        stdscr.addstr(3, 2, "-" * 20)
        stdscr.attroff(curses.color_pair(2))
        
        stdscr.addstr(4, 2, get_cpu_usage())
        stdscr.addstr(5, 2, get_mem_usage())
        stdscr.addstr(6, 2, get_disk_usage())

        # Project Stats
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(8, 2, "PROJECT STATUS")
        stdscr.addstr(9, 2, "-" * 20)
        stdscr.attroff(curses.color_pair(2))
        
        stdscr.addstr(10, 2, get_git_status())
        stdscr.addstr(11, 2, f"CWD: {os.getcwd()}")

        # Triumvirate Status (Mock)
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(2, 40, "TRIUMVIRATE")
        stdscr.addstr(3, 40, "-" * 20)
        stdscr.attroff(curses.color_pair(3))

        stdscr.addstr(4, 40, "$MEAT   : ONLINE")
        stdscr.addstr(5, 40, "$AIMEAT : ACTIVE")
        stdscr.addstr(6, 40, "$THESPY : MONITORING")

        # Refresh
        stdscr.refresh()
        
        # Wait for next update
        time.sleep(REFRESH_RATE)

        # Check for user input (q to quit)
        stdscr.nodelay(True)
        k = stdscr.getch()
        if k == ord('q'):
            break

def main():
    curses.wrapper(draw_menu)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Dashboard Terminated.")
