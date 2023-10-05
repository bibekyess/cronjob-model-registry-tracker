import yaml
from mlflow import MlflowClient
import subprocess
import logging
import requests

logger=logging.getLogger('kfp_logger')
logger.setLevel(logging.INFO)


def get_current_model_uri(deployment_file_remote):
    response = requests.get(deployment_file_remote)
    deployment_yaml = yaml.safe_load(response.content)
    model_uri = deployment_yaml['spec']['predictors'][0]['graph']['modelUri']
    return model_uri


def get_updated_model_uri(model_name):
    client = MlflowClient()
    source = ''
    for mv in client.search_model_versions(f"name='{model_name}'"):
        mv = dict(mv)
        if mv['current_stage'] == 'Production':
            source = mv['source']
    return source

def pull_production_git_repo():    
    completed_process = subprocess.run(['git', 'pull', '--force', 'origin', 'main'], capture_output=True)
    logger.info(completed_process.stdout)
    logger.info(completed_process.stderr)
    logger.info("Pulling the github production repo succeded succesfully!!")


def check_and_update_model_uri(current_model_uri, latest_model_uri, deployment_file_path):
    if current_model_uri != latest_model_uri:

        # It is important to make sure we add config
        subprocess.run(['git', 'config', '--global', 'user.name', '"model-registry-bot"'], capture_output=True)
        subprocess.run(['git', 'config', '--global', 'user.email', '"model-registry-bot@ali.ac.kr'], capture_output=True)

        # First pull the repo and then update otherwise need to stash
        pull_production_git_repo()

        # Update the modelUri in the deployment.yaml file
        with open(deployment_file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
            yaml_data['spec']['predictors'][0]['graph']['modelUri'] = latest_model_uri

        with open(deployment_file_path, 'w') as yaml_file:
            yaml.dump(yaml_data, yaml_file, default_flow_style=False)
    
        completed_process = subprocess.run(['git', 'add', deployment_file_path], capture_output=True)
        logger.info(completed_process.stdout)
        completed_process = subprocess.run(['git', 'commit', '-m', 'Auto update modelUri in deployment.yaml'], capture_output=True)
        logger.info(completed_process.stdout)
        completed_process = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True)
        logger.info(completed_process.stdout)
        return "Changed and committed!!"
    
    return "No change!!"
