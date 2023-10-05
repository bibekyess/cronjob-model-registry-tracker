import requests
import yaml
from mlflow import MlflowClient
import subprocess

def download_deployment_file(file_url):
    response = requests.get(file_url)
    file_name_time_token = file_url.split("/")[-1]
    file_name = file_name_time_token.split("?")[0]

    # Check if the request was successful
    if response.status_code == 200:
        # Extract the file name from the URL
        with open(file_name, "wb") as file:
            file.write(response.content)
        print("File downloaded successfully.")
    else:
        print(f"Failed to download the file. Error code: {response.status_code}")

    return file_name

def get_current_model_uri(deployment_file_path):
    with open(deployment_file_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
        model_uri = yaml_data['spec']['predictors'][0]['graph']['modelUri']
    return model_uri


def get_updated_model_uri(model_name):
    client = MlflowClient()
    source = ''
    for mv in client.search_model_versions(f"name='{model_name}'"):
        mv = dict(mv)
        if mv['current_stage'] == 'Production':
            source = mv['source']
    return source

# Function to check if the modelURI in the deployment.yaml file matches the MLFlow registry
def check_and_update_model_uri(deployment_file_path, production_model):
    current_model_uri = get_current_model_uri(deployment_file_path)

    # Replace with your logic to fetch the latest model URI from MLFlow
    latest_model_uri = get_updated_model_uri(production_model)
    print("Current_model_uri: ", current_model_uri)
    print("Latest_model_uri: ", latest_model_uri)

    if current_model_uri != latest_model_uri:
        print("changed!!")
        subprocess.run(['git', 'config', '--global', 'user.name', '"model-registry-bot"'], capture_output=True)
        subprocess.run(['git', 'config', '--global', 'user.email', '"model-registry-bot@ali.ac.kr'], capture_output=True)
        
        completed_process = subprocess.run(['git', 'pull', '--force', 'origin', 'main'], capture_output=True)

        # Log the captured stdout and stderr
        print("Captured stdout:")
        print(completed_process.stdout)
        print("Captured stderr:")
        print(completed_process.stderr)

        with open(deployment_file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
            yaml_data['spec']['predictors'][0]['graph']['modelUri'] = latest_model_uri

        with open(deployment_file_path, 'w') as yaml_file:
            yaml.dump(yaml_data, yaml_file, default_flow_style=False)

        subprocess.run(['git', 'add', deployment_file_path], capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Auto update modelUri in deployment.yaml'], capture_output=True)
        subprocess.run(['git', 'push', '--force', 'origin', 'main'], capture_output=True)

        # For debugging pass the infinite loop to access the container
        # while True:
        #     pass