import os
from rich.console import Console
from rich.table import Table

proc_folder = '/proc'

# Function to check if a string contains any digits
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
    
    # Try to read the status file
    try:
        with open(status_file, 'r') as f:
            status = f.read()
    except FileNotFoundError:
        return None
    
    name = None
    ppid = None
    uid = None
    
    # Process each line in the status file
    for line in status.splitlines():
        if line.startswith("Name:"):
            name = line.split()[1]
        elif line.startswith("PPid:"):
            ppid = line.split()[1]
        elif line.startswith("Uid:"):
            uid_str = line.split()[1]
            if uid_str.isdigit():
                uid = get_username(int(uid_str))
        
        # If all values are found, break out of the loop
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

def display_processes():
    console = Console()
    processes = list_processes()
    
    table = Table(show_header=True, header_style="red")
    table.add_column("Name", style="bold green", width=30)
    table.add_column("PID", style="cyan")
    table.add_column("PPid", style="cyan")
    table.add_column("User", style="yellow")
    table.add_column("State", style="magenta")
    table.add_column("Memory", style="blue")

    for pid in processes:
        proc_info = read_proc_status_file(pid)
        if proc_info:
            name, ppid, username = proc_info
            state = get_proc_state(pid)
            memory = get_proc_memory(pid)
            table.add_row(name, pid, ppid, username, state, memory or "N/A")

    console.print(table)

if __name__ == "__main__":
    display_processes()
