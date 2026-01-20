# Anvil Kernel: kernel/sched/core.py

tasks = []
current_task = None

class Task:
    def __init__(self, name, pid):
        self.name = name
        self.pid = pid
        self.state = "RUNNABLE"

def init_sched():
    print("[KERNEL] Scheduler initialized")
    global current_task
    current_task = Task("init", 1)
    tasks.append(current_task)

def schedule():
    global current_task
    # Simple Round Robin
    idx = tasks.index(current_task)
    next_idx = (idx + 1) % len(tasks)
    current_task = tasks[next_idx]
    # print(f"[SCHED] Switched to task {current_task.pid} ({current_task.name})")

def spawn(name):
    pid = len(tasks) + 1
    t = Task(name, pid)
    tasks.append(t)
    return pid
