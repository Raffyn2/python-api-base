# Dapr Setup Guide

## Prerequisites

- Docker and Docker Compose
- Python 3.12+
- Dapr CLI (for local development)

## Local Development

### 1. Install Dapr CLI

```bash
# Windows (PowerShell)
powershell -Command "iwr -useb https://raw.githubusercontent.com/dapr/cli/master/install/install.ps1 | iex"

# macOS/Linux
curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | /bin/bash
```

### 2. Initialize Dapr

```bash
dapr init
```

### 3. Start with Docker Compose

```bash
cd deployments/dapr
docker-compose -f docker-compose.dapr.yaml up -d
```

### 4. Run Application

```bash
# With Dapr sidecar
dapr run --app-id python-api --app-port 8000 --dapr-http-port 3500 -- python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Kubernetes Deployment

### 1. Install Dapr on Cluster

```bash
dapr init -k
```

### 2. Apply Components

```bash
kubectl apply -f deployments/k8s/dapr/components/
kubectl apply -f deployments/k8s/dapr/config/
```

### 3. Deploy Application

```bash
kubectl apply -f deployments/k8s/dapr/deployment.yaml
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DAPR_ENABLED` | Enable Dapr integration | `true` |
| `DAPR_HTTP_ENDPOINT` | Dapr HTTP endpoint | `http://localhost:3500` |
| `DAPR_GRPC_ENDPOINT` | Dapr gRPC endpoint | `localhost:50001` |
| `DAPR_API_TOKEN` | API token for authentication | `null` |
| `DAPR_APP_ID` | Application ID | `python-api` |

### Component Files

- `deployments/dapr/components/statestore.yaml` - Redis state store
- `deployments/dapr/components/pubsub.yaml` - Kafka pub/sub
- `deployments/dapr/components/secretstore.yaml` - Secret store
- `deployments/dapr/components/bindings.yaml` - Input/output bindings

### Resiliency Configuration

Edit `deployments/dapr/config/resiliency.yaml` to configure:

- Timeouts
- Retry policies
- Circuit breakers

## Troubleshooting

### Check Dapr Status

```bash
dapr status
```

### View Logs

```bash
# Docker Compose
docker-compose -f docker-compose.dapr.yaml logs python-api-dapr

# Kubernetes
kubectl logs -l app=python-api -c daprd
```

### Health Check

```bash
curl http://localhost:3500/v1.0/healthz
```

### Metadata

```bash
curl http://localhost:3500/v1.0/metadata
```
