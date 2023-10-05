import os
import subprocess
import mlflow.pyfunc
import yaml
from mlflow import MlflowClient
import requests
import time

mlflow.set_tracking_uri('http://192.168.0.29:5000') # FIXME

# Define the path to your deployment.yaml file
deployment_file_remote = "https://raw.githubusercontent.com/bibekyess/model-registry-tracker/main/deployment.yaml"
# Append the query parameter with the current timestamp
timestamp = int(time.time())
deployment_file_remote_with_timestamp = f"{deployment_file_remote}?token={timestamp}"

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

deployment_file = download_deployment_file(deployment_file_remote_with_timestamp)

# Function to get the current modelURI from the deployment.yaml file
def get_current_model_uri():
    with open(deployment_file, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
        model_uri = yaml_data['spec']['predictors'][0]['graph']['modelUri']
    return model_uri

logged_model = 'cross-encoder-sendoncore'

def get_updated_model_uri(model_name):
    client = MlflowClient()
    source = ''
    for mv in client.search_model_versions(f"name='{model_name}'"):
        mv = dict(mv)
        if mv['current_stage'] == 'Production':
            source = mv['source']
    return source

# Function to check if the modelURI in the deployment.yaml file matches the MLFlow registry
def check_and_update_model_uri():
    current_model_uri = get_current_model_uri()

    latest_model_uri = get_updated_model_uri(logged_model)
    print("Current_model_uri: ", current_model_uri)
    print("Latest_model_uri: ", latest_model_uri)

    if current_model_uri != latest_model_uri:
        print("changed!!")
        subprocess.run(['git', 'config', '--global', 'user.name', '"model-registry-bot"'])
        subprocess.run(['git', 'config', '--global', 'user.email', '"model-registry-bot@ali.ac.kr'])
        subprocess.run(['git', 'pull', '--force', 'origin', 'main'])
        
        # Update the modelUri in the deployment.yaml file
        with open(deployment_file, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
            yaml_data['spec']['predictors'][0]['graph']['modelUri'] = latest_model_uri

        with open(deployment_file, 'w') as yaml_file:
            yaml.dump(yaml_data, yaml_file, default_flow_style=False)

        # Commit the updated deployment.yaml file to Git
        subprocess.run(['git', 'add', deployment_file])
        subprocess.run(['git', 'commit', '-m', 'Auto update modelUri in deployment.yaml'])
        subprocess.run(['git', 'push', '--force', 'origin', 'main'])

        # For debugging pass the infinite loop to access the container
        # while True:
        #     pass

if __name__ == "__main__":
    check_and_update_model_uri()
