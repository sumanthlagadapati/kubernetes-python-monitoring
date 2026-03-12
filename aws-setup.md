# AWS Deployment Guide - Kubernetes Python Monitoring

This guide explains how to deploy the project to **Amazon EKS** using **Amazon ECR**.

## 1. Setup Amazon ECR (Elastic Container Registry)

Create a repository for your application:

```bash
# Create repository
aws ecr create-repository --repository-name python-monitoring-app --region <your-region>

# Authenticate Docker to ECR
aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.<your-region>.amazonaws.com

# Build, Tag, and Push
docker build -t python-monitoring-app .
docker tag python-monitoring-app:latest <aws_account_id>.dkr.ecr.<your-region>.amazonaws.com/python-monitoring-app:latest
docker push <aws_account_id>.dkr.ecr.<your-region>.amazonaws.com/python-monitoring-app:latest
```

## 2. Setup Amazon EKS Cluster

The easiest way to create a cluster is using `eksctl`:

```bash
eksctl create cluster \
  --name monitoring-cluster \
  --region <your-region> \
  --with-oidc \
  --nodegroup-name standard-nodes \
  --node-type t3.medium \
  --nodes 2 \
  --managed
```

## 3. Install AWS Load Balancer Controller

Required for the Ingress (ALB/NLB) to work:

```bash
# 1. Create IAM Service Account
eksctl create iamserviceaccount \
  --cluster=monitoring-cluster \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name "AmazonEKSLoadBalancerControllerRole" \
  --attach-policy-arn=arn:aws:iam::<aws_account_id>:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

# 2. Install using Helm
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=monitoring-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

## 4. Deploy Application

Update `manifests/deployment.yaml` with your ECR image URI, then apply:

```bash
kubectl apply -f manifests/
```

## 5. Deploy Monitoring

```bash
kubectl apply -f monitoring/prometheus-grafana.yaml
```

## 6. Access Application

Get the ALB DNS:
```bash
kubectl get ingress -n python-app
```
