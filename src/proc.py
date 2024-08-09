import os

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


processes = list_processes()
for pid in processes:
    proc_info = read_proc_status_file(pid)
    if proc_info:
        name, ppid, username = proc_info
        print(f"Process:    {name},    PPid:    {ppid},    User:    {username}")
