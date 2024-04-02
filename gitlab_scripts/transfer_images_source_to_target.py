import os
import requests
import subprocess

def get_project_id(gitlab_api, project_search, private_token):
    response = requests.get(f'{gitlab_api}/projects?search={project_search}', headers={"Private-Token": private_token})
    response.raise_for_status() 
    return response.json()[0]['id']

def get_repository_ids_and_names(gitlab_api, project_id, private_token):
    response = requests.get(f"{gitlab_api}/projects/{project_id}/registry/repositories?per_page=10000", headers={"Private-Token": private_token})
    response.raise_for_status()
    return [{'id': repo['id'], 'name': repo['name']} for repo in response.json()]

def get_tags(gitlab_api, project_id, repo_id, private_token):
    response = requests.get(f"{gitlab_api}/projects/{project_id}/registry/repositories/{repo_id}/tags", headers={"Private-Token": private_token})
    response.raise_for_status()
    return [tag['name'] for tag in response.json()]

def docker_login(registry_url, username, password):
    command = ["docker", "login", registry_url, "-u", username, "--password-stdin"]
    completed_process = subprocess.run(command, input=password.encode() + b'\n')
    
    if completed_process.returncode != 0:
        print("Docker login failed. Error message:")
        print(completed_process.stderr.decode())

def main():
    SOURCE_PROJECT_PATH = os.environ.get('SOURCE_PROJECT_PATH')
    DEST_PROJECT_PATH = os.environ.get('DEST_PROJECT_PATH')
    SOURCE_GROUP = os.environ.get('SOURCE_GROUP')
    DEST_GROUP = os.environ.get('DEST_GROUP')
    SOURCE_REGISTRY = os.environ.get('SOURCE_REGISTRY')
    DEST_REGISTRY = os.environ.get('DEST_REGISTRY')
    GITLAB_API_SOURCE = os.environ.get('GITLAB_API_SOURCE')
    GITLAB_API_DEST = os.environ.get('GITLAB_API_DEST')
    IMAGE_SOURCE_PORT = os.environ.get('IMAGE_SOURCE_PORT')
    IMAGE_TARGET_PORT = os.environ.get('IMAGE_TARGET_PORT')
    PRIVATE_TOKEN_SOURCE = os.environ.get('PRIVATE_TOKEN_SOURCE')
    PRIVATE_TOKEN_DEST = os.environ.get('PRIVATE_TOKEN_DEST')
    SOURCE_USERNAME = os.environ.get('SOURCE_USERNAME')
    DEST_USERNAME = os.environ.get('DEST_USERNAME')

    source_project_id = get_project_id(gitlab_api_source,source_project_path,PRIVATE_TOKEN_SOURCE)
    dest_project_id = get_project_id(gitlab_api_dest,dest_project_path,PRIVATE_TOKEN_DEST)
    repositories = get_repository_ids_and_names(gitlab_api_source, source_project_id, PRIVATE_TOKEN_SOURCE)

    print(f'total images: {len(repositories)}')
    count = 0
    for repo in repositories:
        repo_id = repo['id']
        repo_name = repo['name']
        tags = get_tags(gitlab_api_source, source_project_id, repo_id, PRIVATE_TOKEN_SOURCE)
        for tag in tags:
            count += 1
            docker_login(source_registry, SOURCE_USERNAME, PRIVATE_TOKEN_SOURCE)
            image_source = f"{source_registry}:{image_source_port}/{source_group}/{source_project_path}/{repo_name}:{tag}"
            image_dest = f"{dest_registry}:{image_target_port}/{dest_group}/{dest_project_path}/{repo_name}:{tag}"
            subprocess.run(["docker", "pull", image_source])
            subprocess.run(["docker", "tag", image_source, image_dest])
            docker_login(dest_registry, DEST_USERNAME, PRIVATE_TOKEN_DEST)
            subprocess.run(["docker", "push", image_dest])
        break

    print("Image transfer complet. Total: ",count)

if __name__ == "__main__":
    main()
