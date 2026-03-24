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
ILLUMIO_PP_ID = str(os.getenv('ILLUMIO_PP_ID', '0'))
ILLUMIO_ORG = str(os.getenv('ILLUMIO_ORG', '1'))

def pp_key_create():
    endpoint = f'/orgs/{ILLUMIO_ORG}/pairing_profiles/{ILLUMIO_PP_ID}/pairing_key'
    url = f'https://{ILLUMIO_API_URL}/api/v2{endpoint}'
    # Body should be empty
    body = {}
    # Set file name for artfactory for 
    ppac_name = f'PPAC_CC_{os.getenv("CI_PIPELINE_ID")}'
    response = requests.post(url, json=body, auth=(ILLUMIO_API_USERNAME, ILLUMIO_API_SECRET), verify=False)
    response_json = response.json()
#    print(f'caly ouput: {response_json}')
    result = response_json.get("activation_code")

     # Save to file 
    with open("build/" + ppac_name, 'w') as f: 
        f.write(result)
    
    comment = f'---> Pairing Provile Activtion Code {response_json.get("result")} has been saved to file: build/{ppac_name}'
    print(comment)
    return result


if __name__ == "__main__":
    if len(sys.argv) < 1:
        print("Usage: python3 pp.py [create] [optional_param]")
        sys.exit(1)

    action = sys.argv[1]

    if action == "create":
        result = pp_key_create()
        print(result)

    else:
        print("Invalid action. Usage: python3 pp.py [create] [optional_param]")
