import os
import requests
import urllib3
import sys

## Suppress warnings about certificate verification being disabled
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Retrieve Illumio API credentials and base URL from environment variables
ILLUMIO_API_USERNAME = str(os.getenv('ILLUMIO_API_USERNAME', 'default_username'))
ILLUMIO_API_SECRET = str(os.getenv('ILLUMIO_API_SECRET', 'default_password'))
ILLUMIO_API_URL = str(os.getenv('ILLUMIO_API_URL', 'https://default_illumio_api_url/api/v2'))
ILLUMIO_CC_NAME = str(os.getenv('ILLUMIO_CC_NAME', 'CC'))
ILLUMIO_CC_DESCRIPTION = str(os.getenv('ILLUMIO_CC_DESCRIPTION', 'Container Cluster created by Gitlab pipeline'))
ILLUMIO_ORG = str(os.getenv('ILLUMIO_ORG', '1'))

# Function to make a GET request to retrieve container cluster information
def cc_get(cc_href=None):
    if cc_href:
        endpoint = f'{cc_href}'
        print("--->>> if yes", endpoint)
    else:
        endpoint = f'/orgs/{ILLUMIO_ORG}/container_clusters'
        print("--->>> if not", endpoint)
    
    url = f'https://{ILLUMIO_API_URL}/api/v2{endpoint}'
    print("--->>> url: ", url)
    
    response = requests.get(url, auth=(ILLUMIO_API_USERNAME, ILLUMIO_API_SECRET), verify=False)
    print("--->>> respones: ", response)
    response_json = response.json()
    print("--->>> response_json: ", response_json)
    
    if isinstance(response_json, list):
        # Extract the desired fields from each object in the list
        results = []
        for item in response_json:
            result = {
                "name": item.get("name"),
                "description": item.get("description"),
                "href": item.get("href")
            }
            results.append(result)
        return results
    
    result = response_json
    results = []
    results = {
        "name": response_json.get("name"),
        "description": response_json.get("description"),
        "href": response_json.get("href")
    }
    return results



# Function to create a container cluster
def cc_create(name, description):
    endpoint = f'/orgs/{ILLUMIO_ORG}/container_clusters'
    url = f'https://{ILLUMIO_API_URL}/api/v2{endpoint}'
    
    # preparing name and description to differentiate a new object
    cc_name = f'CC_{os.getenv("CI_PIPELINE_ID")}'
    cc_description = f'Created by CI Pipeline ID #{os.getenv("CI_PIPELINE_ID")}, Job ID #{os.getenv("CI_JOB_ID")} at {os.getenv("CI_JOB_STARTED_AT")}'

    body = {
        "name": cc_name,
        "description": cc_description
    }
    print("endpoint: ", endpoint)
    print("url: ", url)
    print("ILLUMIO_API_USERNAME:", ILLUMIO_API_USERNAME)
    print("ILLUMIO_API_SECRET :", ILLUMIO_API_SECRET)
    response = requests.post(url, json=body, auth=(ILLUMIO_API_USERNAME, ILLUMIO_API_SECRET), verify=False)
    response_json = response.json()
    print("--->>> response_json: ", response_json)

    # Extract the container_cluster_token from the API response
    container_cluster_token = response_json.get("container_cluster_token")
    
    # Set the container_cluster_token as a bash environment variable
    os.environ.copy()
    os.environ['ILLUMIO_CONTAINER_CLUSTER_TOKEN'] = container_cluster_token

    # Extract the desired fields
    result = {
        "href": response_json.get("href"),
        "name": response_json.get("name"),
        "description": response_json.get("description"),
        "container_cluster_token": response_json.get("container_cluster_token")
    }
    print("result", result)

    # Save to file TOKEN
    with open("build/TOKEN_" + cc_name, 'w') as f: 
        f.write(result.get("container_cluster_token"))
    
    comment = f'---> Container Cluster Token: {response_json.get("container_cluster_token")} has been saved to file: build/TOKEN_{cc_name}'
    print(comment)

    # Save to file HREF (ID)
    with open("build/ID_" + cc_name, 'w') as f: 
        f.write(result.get("href"))
    
    comment = f'---> Container Cluster ID: {response_json.get("href")} has been saved to file: build/ID_{cc_name}'
    print(comment)

    return result
    #return result.get("container_cluster_token")

# Function to delete a container cluster
def cc_delete(cc_href):
    if cc_href.upper() == 'ALL':
        list_url = f'https://{ILLUMIO_API_URL}/api/v2/orgs/{ILLUMIO_ORG}/container_clusters'
        response = requests.get(list_url, auth=(ILLUMIO_API_USERNAME, ILLUMIO_API_SECRET), verify=False)

        if response.status_code != 200:
            return f"Failed to retrieve container clusters: {response.status_code}"
        
        container_clusters = response.json()
        delete_statuses = []
        for cc in container_clusters:
            cc_href = cc['href'].split('/')[-1]
            delete_status = delete_container_cluster(cc_href)
            delete_statuses.append((cc_href, delete_status))
            
        return delete_statuses
    else:
        return delete_container_cluster(cc_href)

def delete_container_cluster(cc_href):
    endpoint = f'/orgs/{ILLUMIO_ORG}/container_clusters/{cc_href}'
    url = f'https://{ILLUMIO_API_URL}/api/v2{endpoint}'
    
    response = requests.delete(url, auth=(ILLUMIO_API_USERNAME, ILLUMIO_API_SECRET), verify=False)

    if response.status_code == 404:
        return "Object not found"
    
    return response.status_code

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 cc.py [create|get|delete] [optional_param]")
        sys.exit(1)

    action = sys.argv[1]

    if action == "create":
        name = ILLUMIO_CC_NAME
        description = ILLUMIO_CC_DESCRIPTION
        result = cc_create(name, description)
        print(result)

    elif action == "get":
        href = None
        if len(sys.argv) > 2:
            href = sys.argv[2]
        result = cc_get(href)
        print(result)

    elif action == "delete":
        if len(sys.argv) < 3:
            print("Please provide the container cluster href to delete")
            sys.exit(1)
        href = sys.argv[2]
        result = cc_delete(href)
        print(result)

    else:
        print("Invalid action. Usage: python3 cc.py [create|get|delete] [optional_param]")
