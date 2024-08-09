import os

proc_folder = '/proc'

# List all files and directories in the specified directory
files_and_dirs = os.listdir(proc_folder)

# Function to check if a string contains any digits
def contains_digits(s):
    return any(char.isdigit() for char in s)

# Print the directories that have integers in their names
for item in files_and_dirs:
    item_path = os.path.join(proc_folder, item)
    if os.path.isdir(item_path) and contains_digits(item):
        print(f'{item}')
