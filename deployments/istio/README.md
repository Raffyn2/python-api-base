# Istio Service Mesh

Configuração do Istio Service Mesh para Python API Base, fornecendo traffic management avançado, segurança mTLS e observabilidade.

## 📁 Estrutura

```
deployments/istio/
├── base/                           # Configuração base
│   ├── kustomization.yaml          # Kustomize base
│   ├── namespace.yaml              # Namespaces com labels
│   ├── istio-operator.yaml         # IstioOperator CRD
│   ├── gateway.yaml                # Istio Gateway
│   ├── virtualservice.yaml         # VirtualService com routing
│   ├── destinationrule.yaml        # DestinationRule com circuit breaker
│   ├── peerauthentication.yaml     # mTLS configuration
│   ├── authorizationpolicy.yaml    # Authorization policies
│   ├── requestauthentication.yaml  # JWT validation
│   └── serviceentry.yaml           # External services
└── overlays/
    ├── dev/                        # Development (PERMISSIVE mTLS)
    ├── staging/                    # Staging (STRICT mTLS)
    └── prod/                       # Production (hardened)
```

## 🚀 Quick Start

### Pré-requisitos

```bash
# Instalar istioctl
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.0 sh -
export PATH=$PWD/istio-1.20.0/bin:$PATH

# Verificar instalação
istioctl version
```

### Instalação

```bash
# Development
kubectl apply -k deployments/istio/overlays/dev

# Staging
kubectl apply -k deployments/istio/overlays/staging

# Production
kubectl apply -k deployments/istio/overlays/prod
```

### Verificação

```bash
# Verificar pods do Istio
kubectl get pods -n istio-system

# Verificar configuração
istioctl analyze deployments/istio/base/

# Verificar mTLS
istioctl authn tls-check my-api.my-api.svc.cluster.local
```

## 🔐 Segurança

### mTLS

O mTLS é configurado por ambiente:

| Ambiente | Modo | Descrição |
|----------|------|-----------|
| Dev | PERMISSIVE | Aceita plain text e mTLS (debugging) |
| Staging | STRICT | Apenas mTLS |
| Prod | STRICT | Apenas mTLS + egress restrito |

### Authorization Policies

```yaml
# Deny-all por padrão
# Apenas tráfego explicitamente permitido passa

# Permitido:
# - Ingress Gateway → API (todas as rotas)
# - API → API (comunicação interna)
# - Prometheus → API (/metrics)
```

### JWT Validation

```yaml
# Configurado em requestauthentication.yaml
issuer: "https://auth.example.com"
jwksUri: "https://auth.example.com/.well-known/jwks.json"
```

## 🚦 Traffic Management

### Canary Deployments

```yaml
# VirtualService com weighted routing
route:
  - destination:
      host: my-api
      subset: stable
    weight: 90
  - destination:
      host: my-api
      subset: canary
    weight: 10
```

### Circuit Breaker

```yaml
# DestinationRule com outlierDetection
outlierDetection:
  consecutive5xxErrors: 5      # Erros para abrir circuito
  interval: 30s                # Janela de análise
  baseEjectionTime: 30s        # Tempo de ejeção
  maxEjectionPercent: 50       # Máximo de pods ejetados
```

### Retry Policy

```yaml
retries:
  attempts: 3
  perTryTimeout: 10s
  retryOn: 5xx,reset,connect-failure
```

## 📊 Observabilidade

### Métricas

Métricas expostas automaticamente pelo Envoy:

- `istio_requests_total` - Total de requests
- `istio_request_duration_milliseconds` - Latência
- `istio_request_bytes` - Bytes recebidos
- `istio_response_bytes` - Bytes enviados

### Tracing

Sampling rate por ambiente:

| Ambiente | Sampling |
|----------|----------|
| Dev | 10% |
| Staging | 5% |
| Prod | 1% |

### Access Logs

Logs em formato JSON com campos:

```json
{
  "timestamp": "...",
  "method": "GET",
  "path": "/api/v1/users",
  "response_code": 200,
  "duration": 45,
  "request_id": "uuid",
  "upstream_host": "10.0.0.1:8080"
}
```

## 🌐 External Services

### ServiceEntry

Serviços externos devem ser declarados:

```yaml
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: external-api
spec:
  hosts:
    - "external-api.example.com"
  ports:
    - number: 443
      protocol: HTTPS
  location: MESH_EXTERNAL
  resolution: DNS
```

### Egress Policy

- **Dev**: `ALLOW_ANY` - permite qualquer egress
- **Staging/Prod**: `REGISTRY_ONLY` - apenas ServiceEntry declarados

## 🔧 Troubleshooting

### Verificar Sidecar Injection

```bash
# Verificar label do namespace
kubectl get ns my-api --show-labels

# Verificar pods com sidecar
kubectl get pods -n my-api -o jsonpath='{.items[*].spec.containers[*].name}'
```

### Debug mTLS

```bash
# Verificar status mTLS
istioctl authn tls-check <pod-name> -n my-api

# Verificar certificados
istioctl proxy-config secret <pod-name> -n my-api
```

### Debug Routing

```bash
# Verificar configuração do Envoy
istioctl proxy-config routes <pod-name> -n my-api

# Verificar clusters
istioctl proxy-config clusters <pod-name> -n my-api
```

### Logs do Envoy

```bash
# Aumentar log level
istioctl proxy-config log <pod-name> --level debug

# Ver logs
kubectl logs <pod-name> -c istio-proxy -n my-api
```

## 📚 Referências

- [Istio Documentation](https://istio.io/latest/docs/)
- [Traffic Management](https://istio.io/latest/docs/concepts/traffic-management/)
- [Security](https://istio.io/latest/docs/concepts/security/)
- [Observability](https://istio.io/latest/docs/concepts/observability/)

---

**Last Updated**: 2025-12-04
**Maintainer**: API Team
