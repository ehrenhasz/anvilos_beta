import sys
import os
import json
import time

# Ensure runtime is in path
sys.path.append(os.path.join(os.path.dirname(__file__), "runtime"))

from synapse import Synapse
from collar import TheCollar

synapse = Synapse("aimeat")
collar = TheCollar("aimeat")

def submit_task():
    # RFC-0044: Build 2 - Drivers
    # Task: VirtIO Net Stub
    correlation_id = f"build2-{int(time.time())}"
    
    card_data = {
        "type": "CODE_CHANGE",
        "context": "oss_sovereignty/sys_09_Anvil/drivers/virtio_net.py",
        "description": "Create a VirtIO Network Driver skeleton. Must include class VirtIONet and a test_init() verification function. Keep it under 50 lines.",
        "source": "AIMEAT",
        "instruction": "WAIT_FOR_LADYSMITH"
    }
    
    print(f"Submitting Card: {correlation_id}")
    
    with synapse._get_cortex_conn() as conn:
        conn.execute("""
            INSERT INTO jobs (correlation_id, idempotency_key, priority, cost_center, payload, status)
            VALUES (?, ?, ?, ?, ?, 'NEEDS_CODING')
        """, (correlation_id, f"op-{correlation_id}", 50, "AIMEAT", json.dumps(card_data)))
        conn.commit()
    
    print("Card Posted. Watching logs...")

if __name__ == "__main__":
    submit_task()
