import os
import requests
import argparse
from dotenv import load_dotenv

SUPPORTED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', # images
    '.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v', '.3gp'    # videos
}

def setup_env():
    global URL, API_KEY
    load_dotenv()

    URL = os.getenv("URL", "").rstrip('/')  # Remove trailing slash
    API_KEY = os.getenv("API_KEY", "")

    if not URL:
        print("❌ ERROR: URL environment variable is not set")
        print("Please set URL in your .env file or environment")
        exit(1)

    if not API_KEY:
        print("❌ ERROR: API_KEY environment variable is not set")
        print("Please set API_KEY in your .env file or environment")
        exit(1)

    return URL, API_KEY

def setup_args(desc, *args):
    parser = argparse.ArgumentParser(description=desc)
    for arg in args:
        parser.add_argument(*arg[:-1], **arg[-1])
    return parser.parse_args()

def make_request(method, endpoint, payload=None, **kwargs):
    full_url = f"{URL}{endpoint}"

    headers = kwargs.get('headers', {})
    headers['x-api-key'] = API_KEY
    headers['Accept'] = 'application/json'

    # Handle different payload types
    if payload is not None:
        if method.upper() in ['POST', 'PUT', 'PATCH']:
            if 'files' not in kwargs: # JSON payload
                headers['Content-Type'] = 'application/json'
                if isinstance(payload, (dict, list)):
                    kwargs['json'] = payload
                else:
                    kwargs['data'] = payload
            else: # File upload with form data
                kwargs['data'] = payload
        elif method.upper() == 'GET':
            kwargs['params'] = payload

    kwargs['headers'] = headers

    response = requests.request(method, full_url, **kwargs)
    response.raise_for_status()
    return response

def validate_directory(path):
    if not os.path.exists(path):
        print(f"❌ Directory {path} does not exist.")
        exit(1)
    if not os.path.isdir(path):
        print(f"❌ Path {path} exists but is not a directory.")
        exit(1)
    return True

def get_all_files(directory):
    files = []
    for root, dirs, filenames in os.walk(directory):
        dirs.sort()
        for filename in sorted(filenames):
            filepath = os.path.join(root, filename)
            if os.path.isfile(filepath):
                files.append(filepath)
    return files

setup_env()
