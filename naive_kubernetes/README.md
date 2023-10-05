# Cronjob Model Registry Tracker using Kubernetes Object

### Setup SSH Key

```bash
cd naive_kubernetes
mkdir ssh-key
ssh-keygen
# Enter the <absolute path to ssh-key directory>
```

### Build Docker Image
Build the Docker image for the tracker using the generated SSH keys:
```bash
docker build -t bibekyess/kfp-model-registry-tracker:v1 --build-arg ssh_prv_key="$(cat ./ssh-key/id_rsa)" --build-arg ssh_pub_key="$(cat ./ssh-key/id_rsa.pub)" .
```

### Build Cronjob Resource
```bash
kubectl apply -f cronjob.yaml
```