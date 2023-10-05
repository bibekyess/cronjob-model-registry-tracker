import mlflow
import utilities as utilities
from kfp import dsl
from kfp.client import Client
from kfp import compiler
import requests
import time

@dsl.component(base_image='bibekyess/kfp-model-registry-tracker:v1',
               target_image='bibekyess/granular-cronjob:v2.3')
def get_model_uri_from_production_repo_op(deployment_file_remote: str)-> str:
    timestamp = int(time.time())
    deployment_file_remote_with_timestamp = f"{deployment_file_remote}?token={timestamp}"
    return utilities.get_current_model_uri(deployment_file_remote_with_timestamp)


@dsl.component(base_image='bibekyess/kfp-model-registry-tracker:v1',
               target_image='bibekyess/granular-cronjob:v2.3',
               packages_to_install=['mlflow==2.6.0'])
def get_model_uri_from_model_registry_op(mlflow_tracking_uri: str, production_model: str) -> str:
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    return utilities.get_updated_model_uri(model_name=production_model)


@dsl.component(base_image='bibekyess/kfp-model-registry-tracker:v1',
               target_image='bibekyess/granular-cronjob:v2.3')
def compare_and_commit_op(prodction_repo_uri: str, model_registry_uri: str, deployment_file_path:str) -> str:
    return utilities.check_and_update_model_uri(current_model_uri=prodction_repo_uri, latest_model_uri=model_registry_uri, deployment_file_path=deployment_file_path)


@dsl.pipeline(
    name='cronjob-granular-pipeline',
    description='Pipeline that continously tracks the model registry with granular components'
)
def tracking_pipeline(deployment_file_remote: str, 
                      mlflow_tracking_uri: str,
                      production_model: str
                      )-> str:
    production_repo_uri = get_model_uri_from_production_repo_op(deployment_file_remote=deployment_file_remote)
    model_registry_uri = get_model_uri_from_model_registry_op(mlflow_tracking_uri=mlflow_tracking_uri, production_model=production_model)
    status = compare_and_commit_op(prodction_repo_uri=production_repo_uri.output, model_registry_uri=model_registry_uri.output, deployment_file_path="./deployment.yaml")
    return status.output


def start_tracking_pipeline_run(kfp_host: str, username: str, password: str, namespace: str):

    session = requests.Session()
    response = session.get(kfp_host)

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {"login": username, "password": password}
    session.post(response.url, headers=headers, data=data)
    session_cookie = session.cookies.get_dict()["authservice_session"]

    client = Client(
        host=f"{kfp_host}/pipeline",
        namespace=f"{namespace}",
        cookies=f"authservice_session={session_cookie}",
    )

    custom_experiment = client.create_experiment('Custom Registry tracker granular', namespace=namespace)

    # print(client.list_experiments())
    run = client.create_run_from_pipeline_func(tracking_pipeline, 
                                               experiment_name=custom_experiment.display_name, 
                                               enable_caching=False,
                                               arguments={
                                                    'deployment_file_remote': 'https://raw.githubusercontent.com/bibekyess/model-registry-tracker/main/deployment.yaml', 
                                                    'mlflow_tracking_uri': 'http://192.168.0.29:5000',
                                                    'production_model': 'cross-encoder-sendoncore'
                                               })

    compiler.Compiler().compile(tracking_pipeline, 'tracking_pipeline_modular.yaml')
    
    client.upload_pipeline_version(pipeline_package_path='tracking_pipeline_modular.yaml', 
                                   pipeline_version_name='v4',
                                   pipeline_name = 'tracking_pipeline_modular')
    
    cronjob = client.create_recurring_run(experiment_id=custom_experiment.experiment_id, 
                                          job_name='Cron job tracker modular v2', 
                                          cron_expression="0 */2 * * * *", 
                                          pipeline_package_path='tracking_pipeline_modular.yaml',
                                          max_concurrency=3, enable_caching=False,
                                          params={
                                            'deployment_file_remote': 'https://raw.githubusercontent.com/bibekyess/model-registry-tracker/main/deployment.yaml', 
                                            'mlflow_tracking_uri': 'http://192.168.0.29:5000',
                                            'production_model': 'cross-encoder-sendoncore'
                                            })

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", type=str, required=True, help= "Kubeflow Central Dashboard Username")
    parser.add_argument("--password", type=str, required=True, help= "Kubeflow Central Dashboard Password")
    parser.add_argument("--kfp_host", type=str, default="http://127.0.0.1:8084", help = "Kubeflow pipeline host")
    parser.add_argument("--namespace", type=str, default="kubeflow-user-example-com", help = "Namespace to run the pipeline")    
    args = parser.parse_args()

    username = args.username
    password = args.password
    kfp_host = args.kfp_host
    namespace = args.namespace
    print(username)
    print(password)
    print(kfp_host)
    print(namespace)
    
    start_tracking_pipeline_run(kfp_host=kfp_host, username=username, password=password, namespace=namespace)
