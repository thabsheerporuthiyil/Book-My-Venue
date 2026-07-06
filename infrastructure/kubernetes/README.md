# Kubernetes (EKS) Deployment Configurations

This directory contains the Kubernetes manifests (or Helm charts) required to deploy the Book My Venue microservices ecosystem to an Amazon EKS cluster or any standard Kubernetes environment.

---

## Folder Layout Strategy

As we migrate towards Kubernetes orchestration, configurations will be structured as follows:

```text
infrastructure/kubernetes/
├── base/                   # Base manifests used across all environments (Kustomize or plain YAML)
│   ├── auth-service/       # Deployment, Service, HPA for Auth
│   ├── venue-service/      # Deployment, Service, HPA for Venues
│   ├── booking-service/
│   └── api-gateway/        # Ingress configurations (e.g., NGINX Ingress Controller rules)
├── overlays/               # Environment-specific overrides
│   ├── staging/            # Staging ConfigMaps, Secrets, replica counts
│   └── production/         # Production ConfigMaps, Secrets, replica counts
└── helm/                   # (Alternative) Helm charts if packaging the platform as a release
    └── bookmyvenue/
```

---

## Migration Path from Docker Compose

The local `docker-compose.yml` serves as the blueprint for these manifests:

1. **Services to Deployments**: Each service defined in docker-compose becomes a Kubernetes `Deployment` to manage Pod replicas.
2. **Ports to Services**: Docker exposed ports become Kubernetes `Service` objects (ClusterIP) for internal networking.
3. **Gateway to Ingress**: The custom NGINX API Gateway will be replaced or supplemented by a Kubernetes `Ingress` resource (e.g., AWS ALB Ingress Controller or NGINX Ingress Controller), offloading SSL termination and external routing to the cluster infrastructure.
4. **Environment Variables**: `.env` configurations move to Kubernetes `ConfigMap` and `Secret` objects.

**Note on Infrastructure:** The underlying EKS Cluster itself, along with managed databases (RDS) and caches (ElastiCache), will be provisioned by Terraform in `infrastructure/terraform/`.
