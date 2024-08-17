# PROC_MONITOR - README
## Overview

proc_monitor is a simple command-line tool that lets you monitor processes running on your Linux system. It displays key details like the process name, ID, parent process ID, user, state, memory usage, and CPU usage in real-time.
Features
- Real-Time Updates: The process list refreshes every second.
- Detailed Information: Shows the essential details for each process, including memory and CPU usage.

## How It Works

The app reads information from the /proc directory, which contains data on all running processes in Linux. It calculates the CPU usage of each process over a one-second period and displays this information in a table format.
Requirements

```
Python 3.8+
Linux 
```

## Running the App

 Install the necessary Python packages:


 ```
 git clone https://github.com/CerberusV1/proc_monitor
                                                                                                                                         
 cd proc_monitor

 pip install -r requirements.txt

 python3 main.py
```

The table will automatically update every second to reflect the current state of your system’s processes.
