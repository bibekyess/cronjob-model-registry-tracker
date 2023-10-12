# Cronjob Model Registry Tracker using Kubeflow Pipelines

### Setup SSH Key

```bash
cd kubeflow_pipelines
mkdir ssh-key
ssh-keygen
# Enter the <absolute path to ssh-key directory>
```

### Build Docker Image
Build the Docker image for the tracker using the generated SSH keys:
```bash
docker build -t bibekyess/kfp-model-registry-tracker:v1 --build-arg ssh_prv_key="$(cat ./ssh-key/id_rsa)" --build-arg ssh_pub_key="$(cat ./ssh-key/id_rsa.pub)" .
```

### Build KFP Component
Use the following command to build the KFP component:
```bash
kfp component build ./src --component-filepattern tracker_pipeline.py --push-image
```
**Note:** The `kfp component build` command adds `WORKDIR /usr/local/src/kfp/components` in the Dockerfile to make it the default working directory. But, we need to make the github tracked directory as the working directory so remove that line or simply use mine uploaded Dockerfile.

### Run Pipeline
Run the pipeline using the following command:
```bash
python src/tracker_pipeline.py --username user@example.com --password 12341234
```


## Running Modular Pipelines
In Kubeflow Pipelines, each component is executed as a single container. This repository provides a modular pipeline, separated into three components:
1) get_model_uri_from_production_repo_op
2) get_model_uri_from_model_registry_op
3) compare_and_commit_op

To run the modular pipeline, follow these steps:

### Build KFP Component (Modular)
```bash
kfp component build ./src_modular --component-filepattern tracker_pipeline_modular.py
python src_modular/tracker_pipeline_modular.py
```

**Note:** Cronjobs can also be scheduled from the Kubeflow Dashboard UI using `Recurring Runs`.