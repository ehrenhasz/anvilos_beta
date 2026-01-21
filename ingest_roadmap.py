import os
import sys

# Ensure runtime is in path
sys.path.append(os.path.join(os.path.dirname(__file__), "runtime"))

from synapse import Synapse

def ingest():
    roadmap_path = "DOCS/ANVIL_KERNEL_ROADMAP.md"
    if not os.path.exists(roadmap_path):
        print(f"Error: {roadmap_path} not found.")
        return

    with open(roadmap_path, "r") as f:
        content = f.read()

    agent_id = "aimeat"
    synapse = Synapse(agent_id)
    
    # We are currently on Build 2
    synapse.set_active_plan("ANVIL_KERNEL_ROADMAP", content, current_step=2)
    print("Roadmap ingested into Cortex DB.")

if __name__ == "__main__":
    ingest()
