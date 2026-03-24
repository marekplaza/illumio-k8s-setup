import os

# The CPU limit you want to set
cpu_limit = str(os.getenv('CPU_LIMIT', '666m,'))

# list of files to addopt
file_paths = [
    "build2/illumio/templates/cven/unpair_daemonset.yaml",
    "build2/illumio/templates/cven/daemonset.yaml",
    "build2/illumio/templates/kubelink/deployment.yaml",
    "build2/illumio/templates/storage/statefulset.yaml",  # CLAS etcd storage
]

for file_path in file_paths:
    if not os.path.exists(file_path):
        print(f"Skipping {file_path} (file not found).")
        continue

    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Define the line to insert
    insert_line = f'              cpu: {cpu_limit}\n'

    # Find the right place to insert the line
    for i, line in enumerate(lines):
        if line.strip() == 'limits:' and lines[i-1].strip() == 'resources:':
            insert_index = i + 2  # Adjust this as needed
            break
    else:
        print(f"Could not find the right place to insert cpu limits in {file_path}.")
        insert_index = None

    if insert_index is not None:
        # Insert the line
        lines.insert(insert_index, insert_line)

        # Write the updated content back to the file
        with open(file_path, 'w') as file:
            file.writelines(lines)

        print(f"Updated {file_path} successfully.")