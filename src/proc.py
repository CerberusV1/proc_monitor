import os
import time
from rich.table import Table
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Header, Footer, Static


proc_folder = '/proc'

def contains_digits(s):
    return any(char.isdigit() for char in s)

def get_username(uid):
    try:
        import pwd
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return None

def list_processes():
    arr_of_procs = []
    files_and_dirs = os.listdir(proc_folder)

    for item in files_and_dirs:
        item_path = os.path.join(proc_folder, item)
        if os.path.isdir(item_path) and contains_digits(item):
            arr_of_procs.append(item)  # Append the process ID

    return arr_of_procs

def read_proc_status_file(pid):
    status_file = f"/proc/{pid}/status"
    
    try:
        with open(status_file, 'r') as f:
            status = f.read()
    except FileNotFoundError:
        return None
    
    name = None
    ppid = None
    uid = None
    
    for line in status.splitlines():
        if line.startswith("Name:"):
            name = line.split()[1]
        elif line.startswith("PPid:"):
            ppid = line.split()[1]
        elif line.startswith("Uid:"):
            uid_str = line.split()[1]
            if uid_str.isdigit():
                uid = get_username(int(uid_str))
        
        if name and ppid and uid:
            break
    
    if name and ppid and uid:
        return name, ppid, uid
    else:
        return None

def get_proc_state(pid):
    stat_file = f"/proc/{pid}/stat"
    
    try:
        with open(stat_file, 'r') as f:
            file_content = f.read()
    except FileNotFoundError:
        return None
    
    state_abbrev = file_content.split()[2]
    state = {
        "R": "Running",
        "S": "Sleeping",
        "D": "Disk sleep",
        "Z": "Zombie",
        "T": "Stopped",
        "t": "Tracing stop",
        "W": "Paging",
        "X": "Dead",
        "x": "Dead",
        "K": "Wakekill",
        "P": "Parked",
        "I": "Idle",
    }.get(state_abbrev, "N/A")
    
    return state

def get_proc_memory(pid):
    statm_file = f"/proc/{pid}/statm"
    
    try:
        with open(statm_file, 'r') as f:
            status = f.read()
    except FileNotFoundError:
        return None
    
    resident_str = status.split()[1]
    
    try:
        resident = int(resident_str)
        mem = resident * 4  # Assume 4KB per page
    except ValueError:
        return None
    
    if mem > 1_000_000:
        mem_str = f"{mem / 1_024 / 1_024:.2f} Gb"
    elif mem > 1_000:
        mem_str = f"{mem / 1_024:.2f} Mb"
    else:
        mem_str = f"{mem:.2f} Kb"
    
    return mem_str

def get_total_cpu_time():
    try:
        with open("/proc/stat", "r") as f:
            for line in f:
                if line.startswith("cpu "):
                    total_cpu_time = sum(int(value) for value in line.split()[1:])
                    return total_cpu_time
        raise FileNotFoundError("Total CPU time not found in /proc/stat")
    except IOError as e:
        return str(e)

def get_process_cpu_time(pid):
    stat_file = f"/proc/{pid}/stat"
    
    try:
        with open(stat_file, 'r') as f:
            file_content = f.read()
    except FileNotFoundError:
        return None
    
    fields = file_content.split()
    utime = int(fields[13])
    stime = int(fields[14])
    
    return utime, stime

def calculate_cpu_percentage(duration_secs):
    total_cpu_time_start = get_total_cpu_time()
    pids = list_processes()

    process_cpu_times = []
    for pid_str in pids:
        pid = int(pid_str)
        if pid:
            cpu_time = get_process_cpu_time(pid)
            if cpu_time:
                process_cpu_times.append((pid, cpu_time))

    time.sleep(duration_secs)

    total_cpu_time_end = get_total_cpu_time()
    cpu_usage_results = []

    for pid, (utime_start, stime_start) in process_cpu_times:
        cpu_time = get_process_cpu_time(pid)
        if cpu_time:
            utime_end, stime_end = cpu_time
            total_cpu_time_diff = total_cpu_time_end - total_cpu_time_start
            cpu_time_diff = (utime_end + stime_end) - (utime_start + stime_start)
            max_cpu_usage = 100.0 * cpu_time_diff / total_cpu_time_diff
            cpu_usage_results.append((pid, max_cpu_usage))

    return cpu_usage_results

class ProcessTable(Static):
    def on_mount(self):
        self.update(self.render_table())

    def render_table(self) -> Table:
        table = Table(show_header=True, header_style="red")
        table.add_column("Name", style="bold green", width=30)
        table.add_column("PID", style="cyan")
        table.add_column("PPid", style="cyan")
        table.add_column("User", style="yellow")
        table.add_column("State", style="magenta")
        table.add_column("Memory", style="blue")
        table.add_column("CPU Usage (%)", style="bold red")

        processes = list_processes()
        cpu_usage_results = calculate_cpu_percentage(1)

        for pid in processes:
            proc_info = read_proc_status_file(pid)
            if proc_info:
                name, ppid, username = proc_info
                state = get_proc_state(pid)
                memory = get_proc_memory(pid)
                cpu_usage = next((f"{cpu:.2f}" for p, cpu in cpu_usage_results if str(p) == pid), "N/A")
                table.add_row(name, pid, ppid, username, state, memory or "N/A", cpu_usage)

        return table

    def refresh_table(self):
        self.update(self.render_table())

from multiprocessing import Process, Queue

class PROC_MONITOR(App):
    def __init__(self):
        super().__init__()
        self.cpu_process = None
        self.cpu_queue = Queue()

    def on_mount(self):
        self.set_interval(1, self.refresh_table())  # Refresh table every 1 second

        # Start a separate process for CPU calculation
        self.cpu_process = Process(target=self.calculate_cpu_worker)
        self.cpu_process.start()

    def calculate_cpu_worker(self):
        while True:
            cpu_usage_results = calculate_cpu_percentage(1)
            self.cpu_queue.put(cpu_usage_results)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        self.process_table = ProcessTable()
        self.scroll = VerticalScroll(self.process_table)
        yield self.scroll

    def refresh_table(self):
        self.process_table.refresh_table()

    def on_shutdown(self):
        if self.cpu_process:
            self.cpu_process.terminate()


if __name__ == "__main__":
    app = PROC_MONITOR()
    app.run()
