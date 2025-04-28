#code for automate listing files in your directories. Using os and datetime library.
# before use, install the dependencies on python
# !pip install os
# !pip install datetime

import os
from datetime import datetime as dt

# Define the root directory
root_dir = '.'  # Adjust as needed
interest_folders = ['Ammonia', 'Urea', 'Utilitas']

# Define excluded extensions
excluded_exts = {'.ini', '.gform', '.gdocs', '.docx', '.docs', '.py'}

# Define target module groups
target_modules = ['PKC', 'PKG', 'PKT', 'PSP', 'PIM']

# Initialize the master dictionary
structured_files = {}

# Traverse each interested folder
for interest in interest_folders:
    interest_path = os.path.join(root_dir, interest)
    if not os.path.exists(interest_path):
        continue

    structured_files[interest] = {}

    # Walk through Level folders (subfolder1)
    for level in os.listdir(interest_path):
        level_path = os.path.join(interest_path, level)
        if not os.path.isdir(level_path):
            continue

        # Check if this folder is a Level folder
        if not any(lvl in level for lvl in ['Level 1', 'Level 2', 'Level 3']):
            continue

        if level not in structured_files[interest]:
            structured_files[interest][level] = {}

        # Walk through subfolder2 and beyond
        for subdir2 in os.listdir(level_path):
            subdir2_path = os.path.join(level_path, subdir2)
            if not os.path.isdir(subdir2_path):
                continue

            for root, dirs, files in os.walk(subdir2_path):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in excluded_exts:
                        continue

                    # Get only the filename, not the full path
                    file_name = os.path.basename(file)

                    # Detect module type
                    detected = None
                    for mod in target_modules:
                        if mod in subdir2:  # Check if the module name is in the subfolder name
                            detected = mod
                            break

                    if detected:
                        if detected not in structured_files[interest][level]:
                            structured_files[interest][level][detected] = set()  # Use set to hinder duplicate
                        structured_files[interest][level][detected].add(file_name)  # Add to set

# Write output to a file
timestamp = dt.now().strftime('%d-%m-%Y-%H-%M-%S')
output_file = f'grouped_file_list-{timestamp}.txt'

with open(output_file, 'w', encoding='utf-8') as f:
    for interest, levels in structured_files.items():
        f.write(f"{interest}\n")
        for level, modules in levels.items():
            f.write(f"{level}:\n")
            for module, files in modules.items():
                f.write(f"{module} List Modules:\n")
                for file in sorted(files):  # Sort the files alphabetically
                    f.write(f"- {file}\n")
                f.write("\n")  # Spacing between modules
            f.write("\n")  # Spacing between levels
        f.write("\n")  # Spacing between interest groups

print(f"Output written to {output_file}")
