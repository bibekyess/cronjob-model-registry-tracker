FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git && \
    apt-get clean

RUN mkdir -p ~/.ssh

ARG ssh_prv_key
ARG ssh_pub_key
RUN echo "$ssh_prv_key" > /root/.ssh/id_rsa && \
    echo "$ssh_pub_key" > /root/.ssh/id_rsa.pub && \
    chmod 600 /root/.ssh/id_rsa && \
    chmod 600 /root/.ssh/id_rsa.pub && \
    ssh-keyscan github.com >> /root/.ssh/known_hosts

RUN git clone git@github.com:bibekyess/model-registry-tracker.git 

WORKDIR /app/model-registry-tracker

COPY model_registry_tracker.py .

RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install mlflow==2.6.0

ENV PATH=/app/model-registry-tracker/venv/bin:$PATH

CMD ["python", "model_registry_tracker.py"]
