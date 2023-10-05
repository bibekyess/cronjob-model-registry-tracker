import mlflow
import time
import utilities as utilities
from kfp import dsl
from kfp.client import Client
from kfp import compiler

kfp_endpoint = 'http://localhost:8084'

@dsl.component(base_image='bibekyess/kfp-model-registry-tracker:v1',
               target_image='bibekyess/cronjob:v9', 
               packages_to_install=['mlflow==2.6.0'])

def model_registry_tracker() -> None:
    mlflow.set_tracking_uri('http://192.168.0.29:5000') # FIXME

    # Define the path to your deployment.yaml file
    deployment_file_remote = "https://raw.githubusercontent.com/bibekyess/model-registry-tracker/main/deployment.yaml"
    # Append the query parameter with the current timestamp
    timestamp = int(time.time())
    deployment_file_remote_with_timestamp = f"{deployment_file_remote}?token={timestamp}"

    deployment_file_path = utilities.download_deployment_file(deployment_file_remote_with_timestamp)

    production_model = 'cross-encoder-sendoncore'

    utilities.check_and_update_model_uri(deployment_file_path=deployment_file_path, production_model=production_model)

@dsl.pipeline(
    name='cronjob-pipeline',
    description='Pipeline that continously tracks the model registry'
)
def tracking_pipeline()-> None:
    model_registry_tracker()

def start_tracking_pipeline_run():
    import requests

    USERNAME = "user@example.com"
    PASSWORD = "12341234" 
    NAMESPACE = "kubeflow-user-example-com"
    HOST = "http://127.0.0.1:8084" # your istio-ingressgateway pod ip:8080

    session = requests.Session()
    response = session.get(HOST)

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {"login": USERNAME, "password": PASSWORD}
    session.post(response.url, headers=headers, data=data)
    session_cookie = session.cookies.get_dict()["authservice_session"]

    client = Client(
        host=f"{HOST}/pipeline",
        namespace=f"{NAMESPACE}",
        cookies=f"authservice_session={session_cookie}",
    )

    custom_experiment = client.create_experiment('Custom Registry tracker', namespace=NAMESPACE)

    print(client.list_experiments())
    run = client.create_run_from_pipeline_func(tracking_pipeline, experiment_name=custom_experiment.display_name, enable_caching=False)
    url = f'{kfp_endpoint}/#/runs/details/{run.run_id}'

    compiler.Compiler().compile(tracking_pipeline, 'tracking_pipeline.yaml')
    
    client.upload_pipeline(pipeline_package_path='tracking_pipeline.yaml', pipeline_name='tracking_pipeline')
    cronjob = client.create_recurring_run(experiment_id=custom_experiment.experiment_id, job_name='Cron job tracker', cron_expression="0 */2 * * * *", pipeline_package_path='tracking_pipeline.yaml',
                                          max_concurrency=3, enable_caching=False)
    print(url)

if __name__ == '__main__':
    start_tracking_pipeline_run()