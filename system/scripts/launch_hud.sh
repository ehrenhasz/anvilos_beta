#!/bin/bash
# scripts/launch_hud.sh
# Sets up the "Meat-Space" HUD: Cortex (Left), BigIron (TopRight), Btop (BotRight)

REPO_DIR="/home/aimeat/github/droppod"

# 1. Launch Left Window: Cortex (Gemini)
i3-msg "workspace 1"
xfce4-terminal --title="GEMINI_CORTEX" --geometry=100x40 --command="bash -c 'cd $REPO_DIR && node cortex.js; exec bash'" &
sleep 1

# 2. Split Horizontal (Prepare for Right Side)
i3-msg "split h"

# 3. Launch Top Right: Big Iron
xfce4-terminal --title="BIG_IRON" --command="bash -c 'watch -t -n 0.1 python3 $REPO_DIR/system/dashboard.py'" &
sleep 1

# 4. Split Vertical (Prepare for Bottom Right)
i3-msg "split v"

# 5. Launch Bottom Right: Btop
xfce4-terminal --title="SYSTEM_MONITOR" --command="btop" &

echo ">> HUD INITIALIZED."
