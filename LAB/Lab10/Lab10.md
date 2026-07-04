# Lab 10: Run the Collector on Minikube

## Lab Introduction

The Lab 9 collector is a finite batch process, so Kubernetes should run it as a Job rather than a Deployment. This standalone lab uses demo mode and requires no Cisco sandbox. Learners load the local image into Minikube, apply a ConfigMap and Job, inspect scheduling and logs, then convert the workload into a CronJob.

## Learning Objectives

- Start and inspect Minikube.
- Load a local Docker image into the cluster runtime.
- Apply Namespace, ConfigMap, Job, and CronJob manifests.
- Interpret pod phases, events, logs, restart policy, and backoff limits.
- Configure resource requests and limits.
- Clean up namespaced resources.

## Task 1: Prepare Minikube

```bash
minikube start --driver=docker
kubectl cluster-info
kubectl get nodes -o wide
```

Build the Lab 9 image if it does not exist, then load it:

```bash
cd "$HOME/ccnpauto-workspace/lab9-docker-interface-collector"
docker build -t lab9-interface-collector:1.0 .
minikube image load lab9-interface-collector:1.0
minikube image ls | grep lab9-interface-collector
```

## Task 2: Apply Configuration

Copy the Lab 10 manifests into a new GitLab project, then inspect them:

```bash
kubectl apply -f manifests/namespace.yaml
kubectl apply -f manifests/configmap.yaml
kubectl -n network-automation get configmap interface-collector-config -o yaml
```

The ConfigMap sets `DEMO_MODE=true`, allowing the image to run without network credentials.

## Task 3: Run the Job

```bash
kubectl apply -f manifests/job.yaml
kubectl -n network-automation get jobs,pods
kubectl -n network-automation wait \
  --for=condition=complete job/interface-collector --timeout=120s
kubectl -n network-automation logs job/interface-collector
```

The pod should print the same interface table as Docker. Describe the Job and pod to locate image, environment source, resource controls, restart policy, and events.

## Task 4: Diagnose a Controlled Failure

Temporarily change the image tag in a copy of the manifest to a nonexistent value and apply it under another Job name. Observe `ImagePullBackOff` or `ErrImageNeverPull`:

```bash
kubectl -n network-automation get pods
kubectl -n network-automation describe pod FAILED_POD
```

Delete the failed Job after recording the event. Kubernetes events often explain startup failures before application logs exist.

## Task 5: Schedule the Application

```bash
kubectl apply -f manifests/cronjob.yaml
kubectl -n network-automation get cronjobs
kubectl -n network-automation create job \
  --from=cronjob/scheduled-interface-collector manual-collector
kubectl -n network-automation wait \
  --for=condition=complete job/manual-collector --timeout=120s
kubectl -n network-automation logs job/manual-collector
```

`concurrencyPolicy: Forbid` prevents overlapping executions. History limits prevent completed Jobs from accumulating indefinitely.

## Task 6: Clean Up

```bash
kubectl delete namespace network-automation
minikube stop
```

## Key Takeaways

- Job is the correct controller for finite work; Deployment is intended for continuously running replicas.
- ConfigMaps separate non-secret runtime configuration from images.
- Requests influence scheduling, while limits constrain consumption.
- Events, status, and logs describe different failure layers.
- CronJobs schedule Jobs and require concurrency and history policies.

The next lab connects Git commits to controlled network deployment through GitLab CI/CD.
