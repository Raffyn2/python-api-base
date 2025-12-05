# Knative Serverless Deployment

Configuração de deployment serverless para Python API Base usando Knative 1.15 no Kubernetes.

## Visão Geral

Knative é uma plataforma serverless para Kubernetes que oferece:
- Auto-scaling (incluindo scale-to-zero)
- Traffic management e canary deployments
- Event-driven architecture com CloudEvents
- Integração nativa com Istio para mTLS e observability

## Pré-requisitos

### Cluster Kubernetes

- Kubernetes 1.28+
- kubectl configurado
- Helm 3.14+ (opcional)

### Knative Serving

```bash
# Instalar Knative Serving CRDs
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.15.0/serving-crds.yaml

# Instalar Knative Serving core
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.15.0/serving-core.yaml

# Instalar networking layer (Istio)
kubectl apply -f https://github.com/knative/net-istio/releases/download/knative-v1.15.0/net-istio.yaml
```

### Knative Eventing (Opcional)

```bash
# Instalar Knative Eventing CRDs
kubectl apply -f https://github.com/knative/eventing/releases/download/knative-v1.15.0/eventing-crds.yaml

# Instalar Knative Eventing core
kubectl apply -f https://github.com/knative/eventing/releases/download/knative-v1.15.0/eventing-core.yaml

# Instalar Kafka Source (se usar Kafka)
kubectl apply -f https://github.com/knative-extensions/eventing-kafka-broker/releases/download/knative-v1.15.0/eventing-kafka-source.yaml
```

## Quick Start

### Deploy para Development

```bash
# Aplicar configuração de desenvolvimento
kubectl apply -k deployments/knative/overlays/dev

# Verificar status
kubectl get ksvc -n my-api-dev

# Obter URL do serviço
kubectl get ksvc python-api-base -n my-api-dev -o jsonpath='{.status.url}'
```

### Deploy para Production

```bash
# Aplicar configuração de produção
kubectl apply -k deployments/knative/overlays/prod

# Verificar status
kubectl get ksvc -n my-api
```

## Estrutura de Diretórios

```
deployments/knative/
├── base/
│   ├── kustomization.yaml    # Base Kustomize config
│   ├── service.yaml          # Knative Service definition
│   ├── configmap.yaml        # Application configuration
│   └── serviceaccount.yaml   # RBAC configuration
├── overlays/
│   ├── dev/                  # Development overlay
│   ├── staging/              # Staging overlay
│   └── prod/                 # Production overlay
├── eventing/
│   ├── kafka-source.yaml     # Kafka event source
│   ├── broker.yaml           # Event broker
│   └── trigger.yaml          # Event triggers
├── traffic/
│   ├── canary-deployment.yaml
│   ├── blue-green.yaml
│   └── rollback.yaml
└── README.md
```

## Configuração

### Autoscaling

| Parâmetro | Dev | Staging | Prod | Descrição |
|-----------|-----|---------|------|-----------|
| minScale | 0 | 1 | 2 | Mínimo de réplicas |
| maxScale | 3 | 5 | 20 | Máximo de réplicas |
| target | 50 | 80 | 100 | Concurrency target |
| scale-down-delay | 15s | 30s | 60s | Delay antes de scale down |

### Recursos

| Ambiente | CPU Request | CPU Limit | Memory Request | Memory Limit |
|----------|-------------|-----------|----------------|--------------|
| Dev | 50m | 500m | 128Mi | 512Mi |
| Staging | 100m | 750m | 256Mi | 768Mi |
| Prod | 200m | 2000m | 512Mi | 2Gi |

## Traffic Management

### Canary Deployment

```bash
# Aplicar canary com 10% do tráfego
kubectl apply -f deployments/knative/traffic/canary-deployment.yaml

# Verificar distribuição de tráfego
kubectl get ksvc python-api-base -o jsonpath='{.status.traffic}'
```

### Blue-Green Deployment

```bash
# Deploy nova versão (green) sem tráfego
kubectl apply -f deployments/knative/traffic/blue-green.yaml

# Testar via URL tagged
curl https://green-python-api-base.my-api.example.com/health

# Promover green para produção (editar traffic para 100%)
kubectl patch ksvc python-api-base --type=merge -p '{"spec":{"traffic":[{"revisionName":"python-api-base-green","percent":100}]}}'
```

### Rollback

```bash
# Rollback para versão anterior
kubectl apply -f deployments/knative/traffic/rollback.yaml
```

## Eventing (CloudEvents)

### Configurar Kafka Source

```bash
# Aplicar configuração de eventing
kubectl apply -k deployments/knative/eventing

# Verificar KafkaSource
kubectl get kafkasource -n my-api
```

### Enviar CloudEvent

```bash
curl -X POST https://python-api-base.my-api.example.com/events \
  -H "Content-Type: application/cloudevents+json" \
  -d '{
    "specversion": "1.0",
    "id": "123",
    "source": "/orders",
    "type": "com.example.order.placed",
    "data": {"orderId": "12345"}
  }'
```

### Python CloudEvents Adapter

```python
from fastapi import FastAPI, Depends
from src.infrastructure.eventing import CloudEvent, get_cloud_event

app = FastAPI()

@app.post("/events")
async def handle_event(event: CloudEvent = Depends(get_cloud_event)):
    print(f"Received event: {event.type} from {event.source}")
    return {"status": "processed", "event_id": event.id}
```

## Integração com Istio

O Knative integra automaticamente com Istio quando configurado como networking layer:

- mTLS automático entre serviços
- Authorization policies aplicadas
- Métricas e tracing via Istio

### Verificar mTLS

```bash
istioctl authn tls-check python-api-base.my-api.svc.cluster.local
```

## Integração com ArgoCD

### Aplicar via ArgoCD

```bash
# Aplicar ApplicationSet para todos os ambientes
kubectl apply -f deployments/argocd/applicationsets/knative-api-set.yaml

# Ou aplicar Applications individuais
kubectl apply -f deployments/argocd/applications/knative-api.yaml
```

### Verificar Status

```bash
argocd app list | grep knative
argocd app get python-api-base-knative-prod
```

## Monitoring

### Prometheus Metrics

Métricas disponíveis:
- `revision_request_count` - Total de requests
- `revision_request_latencies` - Latência de requests
- `autoscaler_desired_pods` - Pods desejados pelo autoscaler
- `autoscaler_actual_pods` - Pods atuais

### Grafana Dashboard

Importar dashboard: `deployments/monitoring/grafana-dashboard-knative.json`

### Alerts

Alerts configurados em `deployments/monitoring/prometheus-alerts-knative.yml`:
- High cold start latency (> 3s p95)
- Scaling failures (panic mode)
- High error rate (> 5%)
- Scale-to-zero stuck

## Troubleshooting

### Service não inicia

```bash
# Verificar eventos
kubectl describe ksvc python-api-base -n my-api

# Verificar logs do pod
kubectl logs -l serving.knative.dev/service=python-api-base -n my-api -c user-container

# Verificar revision
kubectl get revision -n my-api
kubectl describe revision <revision-name> -n my-api
```

### Scale-to-zero não funciona

```bash
# Verificar configuração de autoscaling
kubectl get ksvc python-api-base -o yaml | grep -A10 autoscaling

# Verificar activator
kubectl logs -n knative-serving -l app=activator
```

### Cold start lento

1. Verificar tamanho da imagem
2. Verificar probes (initialDelaySeconds)
3. Considerar minScale > 0
4. Usar provisioned concurrency

### Eventos não chegam

```bash
# Verificar KafkaSource
kubectl describe kafkasource python-api-base-kafka-source -n my-api

# Verificar Broker
kubectl get broker -n my-api
kubectl describe broker python-api-base-broker -n my-api

# Verificar Triggers
kubectl get trigger -n my-api
```

## Comparação com Outras Opções Serverless

| Feature | Knative | AWS Lambda | Vercel |
|---------|---------|------------|--------|
| Cold Start | ~1-5s | ~1-3s | ~500ms-2s |
| Max Duration | Configurável | 15min | 30s (Pro) |
| Max Memory | Configurável | 10GB | 3GB |
| Scale-to-Zero | Sim | Sim | Sim |
| VPC Support | Sim (K8s) | Sim | Não |
| Vendor Lock-in | Não | Alto | Médio |
| Custo | Infra K8s | Pay per use | Free tier + uso |
| Event Sources | Kafka, HTTP, etc | AWS services | HTTP |
| Traffic Splitting | Nativo | Via ALB | Nativo |

### Quando usar Knative

- Já tem infraestrutura Kubernetes
- Precisa de portabilidade multi-cloud
- Quer evitar vendor lock-in
- Precisa de integração com Kafka/RabbitMQ
- Quer controle total sobre a infraestrutura

### Quando usar AWS Lambda

- Infraestrutura AWS existente
- Integração com serviços AWS
- Não quer gerenciar Kubernetes
- Workloads esporádicos

### Quando usar Vercel

- Aplicações frontend/fullstack
- Deploy rápido e simples
- Edge functions necessárias
- Não precisa de VPC

## Referências

- [Knative Documentation](https://knative.dev/docs/)
- [Knative Serving](https://knative.dev/docs/serving/)
- [Knative Eventing](https://knative.dev/docs/eventing/)
- [CloudEvents Specification](https://cloudevents.io/)
- [Istio + Knative](https://knative.dev/docs/install/installing-istio/)
