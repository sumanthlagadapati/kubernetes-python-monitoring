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
    kubectl apply -f monitoring/loki-promtail.yaml
    ```

## AWS Implementation

For deploying this project on **Amazon EKS** with **Amazon ECR**, please refer to the [AWS Setup Guide](aws-setup.md).

Key AWS Features:
- **Amazon ECR**: For private image hosting.
- **Amazon EKS**: Managed Kubernetes service.
- **AWS ALB**: Automatically provisioned via Ingress annotations.

## Ansible Automation

You can also deploy the entire stack using Ansible. This automates the application of all Kubernetes manifests.

### Prerequisites (Ansible)
- Ansible installed.
- `kubernetes` Python library installed (`pip install kubernetes`).
- `kubernetes.core` collection installed (`ansible-galaxy collection install kubernetes.core`).

### Run the Deployment
```bash
ansible-playbook -i ansible/inventory.ini ansible/deploy-app.yml
```

This will automatically deploy the application, Prometheus, Grafana, and Loki (with Promtail) for centralized logging.

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

### 4. View Centralized Logs in Grafana

1. In Grafana, go to **Explore**.
2. Select the **Loki** data source.
3. Run log queries (e.g., `{job="varlogs"}`) to view logs collected from your cluster.

### 5. Prebuilt Dashboard Auto-Import

The main Python app monitoring dashboard is now automatically imported into Grafana by the Ansible playbook. After deployment, find it in the Grafana dashboard list as **Python App Monitoring**.

### 6. Custom Prometheus Alert Rules (UI & API)

You can now create your own Prometheus alert rules via the app:

- **Web UI:** Visit `/alerts` on your app (e.g., `http://<app-url>/alerts`) to use a simple form.
- **API:** POST to `/api/alerts` with JSON or form data:
  ```json
  {
    "alert": "HighCPU",
    "expr": "sum(rate(cpu_usage[5m])) > 0.8",
    "for": "1m",
    "severity": "warning",
    "summary": "High CPU usage"
  }
  ```
- Rules are stored in `monitoring/custom_alerts.yaml` and can be included in your Prometheus config.
- **Alert rule names must be unique:**
  Attempting to create a rule with an existing `alert` name will result in an error.
  ```json
  {
    "error": "Alert rule with name 'HighCPU' already exists"
  }
  ```

- **Required fields:**
  Both `alert` and `expr` are required and must be non-empty strings. If either is missing, empty, or not a string, you will receive:
  ```json
  {
    "error": "'alert' and 'expr' are required non-empty strings"
  }
  ```

- **Example of a valid request:**
  ```json
  {
    "alert": "HighCPU",
    "expr": "sum(rate(cpu_usage[5m])) > 0.8",
    "for": "1m",
    "severity": "warning",
    "summary": "High CPU usage"
  }
  ```

- After rule creation, the app triggers a Prometheus reload by POSTing to `/-/reload` on your Prometheus server (default: `http://localhost:9090`).
- You can override the Prometheus URL by setting the `PROMETHEUS_URL` environment variable.

### 6. Auto-scaling (HPA)
Generate load to trigger scaling:
```bash
kubectl run load-gen --image=busybox -it --rm -n python-app -- \
  sh -c "while true; do wget -qO- http://python-app-svc/heavy-work; done"
```
Monitor scaling:
```bash
kubectl get hpa python-app-hpa -n python-app -w
```
