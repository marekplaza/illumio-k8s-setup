file_path = "build2/illumio/templates/cven/unpair_job.yaml"

with open(file_path, 'r') as file:
    lines = file.readlines()

# Define the line to insert
insert_line = '      imagePullSecrets:\n        - name: illumio-pull-secret\n'

# Find the right place to insert the line
for i, line in enumerate(lines):
    if line.strip() == 'spec:':
        # Assuming that 'template' is always directly under 'spec'
        # and 'spec' is always directly under 'template'
        insert_index = i + 4
        break
else:
    print("Could not find the right place to insert imagePullSecrets.")
    insert_index = None

if insert_index is not None:
    # Insert the line
    lines.insert(insert_index, insert_line)
    
    # Write the updated content back to the file
    with open(file_path, 'w') as file:
        file.writelines(lines)
    
    print(f"Updated {file_path} successfully.")

