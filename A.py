import os
import requests

# JFrog ArtifactoryのURLと認証情報
ARTIFACTORY_URL = 'https://your-artifactory-domain/artifactory'
API_URL = f'{ARTIFACTORY_URL}/api/storage'
REPO_KEY = 'your-repo-key'
BASE_DIR = 'your-directory-path'
USERNAME = 'your-username'
PASSWORD = 'your-password'

def download_file(url, local_path):
    response = requests.get(url, auth=(USERNAME, PASSWORD))
    response.raise_for_status()
    with open(local_path, 'wb') as file:
        file.write(response.content)

def download_directory(base_url, local_dir):
    response = requests.get(base_url, auth=(USERNAME, PASSWORD))
    response.raise_for_status()
    data = response.json()
    
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    for item in data['children']:
        item_path = item['uri']
        item_url = f"{base_url}/{item_path.lstrip('/')}"
        local_path = os.path.join(local_dir, item_path.lstrip('/'))

        if item['folder']:
            download_directory(item_url, local_path)
        else:
            download_file(f"{ARTIFACTORY_URL}/{REPO_KEY}/{BASE_DIR}/{item_path.lstrip('/')}", local_path)

if __name__ == "__main__":
    base_url = f"{API_URL}/{REPO_KEY}/{BASE_DIR}"
    local_dir = os.path.basename(BASE_DIR)
    download_directory(base_url, local_dir)
