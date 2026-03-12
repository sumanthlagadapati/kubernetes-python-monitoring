# Kubernetes Python Monitoring Project

This project demonstrates a Python Flask application deployed on Kubernetes with auto-scaling (HPA), monitoring via Prometheus, and visualization via Grafana.

## Project Structure

```
kubernetes-python-monitoring/
├── app.py                  # Flask application with Prometheus metrics
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container definition
├── manifests/              # Kubernetes infrastructure
│   ├── deployment.yaml      # App Deployment + Namespace
│   ├── service-ingress.yaml # Networking
│   └── hpa.yaml             # Auto-scaling configuration
└── monitoring/             # Monitoring stack
    ├── prometheus-grafana.yaml # Prometheus & Grafana stack
    └── grafana-dashboard.json # Grafana dashboard export
```

## Prerequisites

-   Kubernetes cluster (Minikube, Kind, or Cloud)
-   `kubectl` CLI
-   Docker (if building locally)

## Quick Start (Minikube)

1.  **Start Minikube**:
    ```bash
    minikube start
    minikube addons enable ingress
    minikube addons enable metrics-server
    ```

2.  **Build the Image**:
    ```bash
    eval $(minikube docker-env)
    docker build -t python-app:latest .
    ```

3.  **Deploy the Application**:
    ```bash
    kubectl apply -f manifests/
    ```

4.  **Deploy Monitoring Stack**:
    ```bash
    kubectl apply -f monitoring/prometheus-grafana.yaml
    ```

## Verification

### 1. Access the App
```bash
minikube service python-app-svc -n python-app
```

### 2. Check Metrics
Access the `/metrics` endpoint on the application URL.

### 3. Access Monitoring
```bash
# Prometheus
minikube service prometheus-svc -n monitoring

# Grafana
minikube service grafana-svc -n monitoring
# Login: admin / admin123
```

### 4. Auto-scaling (HPA)
Generate load to trigger scaling:
```bash
kubectl run load-gen --image=busybox -it --rm -n python-app -- \
  sh -c "while true; do wget -qO- http://python-app-svc/heavy-work; done"
```
Monitor scaling:
```bash
kubectl get hpa python-app-hpa -n python-app -w
```
