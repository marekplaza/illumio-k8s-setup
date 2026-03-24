import yaml
import os

# Read the values.yaml file
with open("build2/illumio/values.yaml", "r") as f:
    data = yaml.safe_load(f)

# Define the keys we're interested in
keys_of_interest = [
    "registry",
    "repo",
    "imageTag",
    "imagePullPolicy"
]

# Process main sections and their sub-sections
def process_section(prefix, section_data):
    result = []
    for key in keys_of_interest:
        if key in section_data:
            result.append(f"{prefix}_{key}={section_data[key]}")
    return result

output = []

for main_key in ["kubelink", "cven", "storage", "initContainer", "toolbox"]:
    if main_key not in data:
        continue
    output.extend(process_section(main_key, data[main_key]))
    for sub_key, sub_section in data[main_key].items():
        if isinstance(sub_section, dict) and "registry" in sub_section:
            output.extend(process_section(f"{main_key}_{sub_key}", sub_section))

# Write the results to the file
hc_name = f'HC_{os.getenv("CI_PIPELINE_ID")}'
with open("build2/" + hc_name, "w") as f:
    for line in output:
        f.write(line + "\n")

        
