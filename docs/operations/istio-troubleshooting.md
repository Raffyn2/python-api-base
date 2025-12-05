# Istio Service Mesh Troubleshooting Guide

Este runbook fornece procedimentos para diagnosticar e resolver problemas comuns do Istio Service Mesh.

## Índice

- [Verificação de Saúde](#verificação-de-saúde)
- [Problemas de mTLS](#problemas-de-mtls)
- [Problemas de Roteamento](#problemas-de-roteamento)
- [Circuit Breaker](#circuit-breaker)
- [Authorization Policies](#authorization-policies)
- [Egress Traffic](#egress-traffic)
- [Performance](#performance)

---

## Verificação de Saúde

### Verificar Status do Control Plane

```bash
# Status dos pods do Istio
kubectl get pods -n istio-system

# Verificar istiod
kubectl logs -n istio-system -l app=istiod --tail=100

# Verificar ingress gateway
kubectl logs -n istio-system -l app=istio-ingressgateway --tail=100
```

### Verificar Sidecar Injection

```bash
# Verificar label do namespace
kubectl get ns my-api --show-labels

# Verificar se pods têm sidecar
kubectl get pods -n my-api -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].name}{"\n"}{end}'

# Deve mostrar: <pod-name>  my-api  istio-proxy
```

### Analisar Configuração

```bash
# Análise completa
istioctl analyze -n my-api

# Verificar configuração do proxy
istioctl proxy-status

# Verificar sincronização
istioctl proxy-config all <pod-name> -n my-api
```

---

## Problemas de mTLS

### Sintomas

- Conexões recusadas entre serviços
- Erros "connection reset by peer"
- Logs com "TLS handshake failed"

### Diagnóstico

```bash
# Verificar modo mTLS
istioctl authn tls-check <pod-name>.my-api my-api.my-api.svc.cluster.local

# Verificar PeerAuthentication
kubectl get peerauthentication -n my-api -o yaml

# Verificar certificados
istioctl proxy-config secret <pod-name> -n my-api

# Verificar logs do proxy
kubectl logs <pod-name> -c istio-proxy -n my-api | grep -i tls
```

### Soluções

#### Certificado Expirado

```bash
# Forçar rotação de certificado
kubectl delete secret istio-ca-secret -n istio-system
kubectl rollout restart deployment istiod -n istio-system
```

#### Modo mTLS Incompatível

```yaml
# Temporariamente usar PERMISSIVE para debug
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: debug-permissive
  namespace: my-api
spec:
  mtls:
    mode: PERMISSIVE
```

---

## Problemas de Roteamento

### Sintomas

- Requests não chegam ao destino correto
- Canary não recebe tráfego
- 404 ou 503 inesperados

### Diagnóstico

```bash
# Verificar VirtualService
kubectl get virtualservice -n my-api -o yaml

# Verificar rotas do Envoy
istioctl proxy-config routes <pod-name> -n my-api

# Verificar clusters
istioctl proxy-config clusters <pod-name> -n my-api

# Verificar endpoints
istioctl proxy-config endpoints <pod-name> -n my-api
```

### Soluções

#### VirtualService Não Aplicado

```bash
# Verificar se o gateway está correto
kubectl get gateway -n my-api -o yaml

# Verificar se hosts coincidem
istioctl analyze -n my-api
```

#### Subsets Não Encontrados

```bash
# Verificar DestinationRule
kubectl get destinationrule -n my-api -o yaml

# Verificar labels dos pods
kubectl get pods -n my-api --show-labels
```

---

## Circuit Breaker

### Sintomas

- Muitos erros 503
- Pods sendo ejetados do pool
- Latência aumentando

### Diagnóstico

```bash
# Verificar métricas de outlier detection
kubectl exec -it <pod-name> -c istio-proxy -n my-api -- \
  curl localhost:15000/stats | grep outlier

# Verificar clusters com hosts ejetados
istioctl proxy-config clusters <pod-name> -n my-api -o json | \
  jq '.[] | select(.outlier_detection != null)'

# Verificar logs
kubectl logs <pod-name> -c istio-proxy -n my-api | grep -i outlier
```

### Soluções

#### Ajustar Thresholds

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: api-destinationrule
spec:
  host: my-api
  trafficPolicy:
    outlierDetection:
      consecutive5xxErrors: 10      # Aumentar threshold
      interval: 60s                 # Aumentar janela
      baseEjectionTime: 15s         # Reduzir tempo de ejeção
      maxEjectionPercent: 30        # Reduzir % máximo
```

#### Desabilitar Temporariamente

```yaml
# Remover outlierDetection para debug
trafficPolicy:
  connectionPool:
    http:
      http2MaxRequests: 1000
  # outlierDetection: removido
```

---

## Authorization Policies

### Sintomas

- Erros 403 Forbidden
- Requests bloqueados inesperadamente
- Logs com "RBAC: access denied"

### Diagnóstico

```bash
# Verificar policies
kubectl get authorizationpolicy -n my-api -o yaml

# Verificar logs de RBAC
kubectl logs <pod-name> -c istio-proxy -n my-api | grep -i rbac

# Aumentar log level
istioctl proxy-config log <pod-name> -n my-api --level rbac:debug
```

### Soluções

#### Verificar Principals

```bash
# Verificar identidade do caller
kubectl exec -it <caller-pod> -c istio-proxy -n my-api -- \
  curl localhost:15000/certs | jq '.certificates[0].cert_chain[0].subject_alt_names'
```

#### Policy de Debug

```yaml
# Temporariamente permitir todo tráfego
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-all-debug
  namespace: my-api
spec:
  rules:
    - {}  # Permite tudo
```

---

## Egress Traffic

### Sintomas

- Conexões externas falhando
- Erros "connection refused" para APIs externas
- Timeout em chamadas externas

### Diagnóstico

```bash
# Verificar ServiceEntry
kubectl get serviceentry -n my-api -o yaml

# Verificar política de egress
kubectl get istiooperator -n istio-system -o yaml | grep -A5 outboundTrafficPolicy

# Testar conectividade
kubectl exec -it <pod-name> -c istio-proxy -n my-api -- \
  curl -v https://external-api.example.com
```

### Soluções

#### Criar ServiceEntry

```yaml
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: external-api
  namespace: my-api
spec:
  hosts:
    - "external-api.example.com"
  ports:
    - number: 443
      name: https
      protocol: HTTPS
  location: MESH_EXTERNAL
  resolution: DNS
```

#### Temporariamente Permitir Todo Egress

```yaml
# Em IstioOperator
meshConfig:
  outboundTrafficPolicy:
    mode: ALLOW_ANY  # Apenas para debug!
```

---

## Performance

### Sintomas

- Latência alta
- CPU/Memory do sidecar elevados
- Requests lentos

### Diagnóstico

```bash
# Métricas do proxy
kubectl exec -it <pod-name> -c istio-proxy -n my-api -- \
  curl localhost:15000/stats | grep -E "(upstream_rq|downstream_rq)"

# Recursos do sidecar
kubectl top pod <pod-name> -n my-api --containers

# Verificar configuração de recursos
kubectl get pod <pod-name> -n my-api -o yaml | grep -A10 istio-proxy
```

### Soluções

#### Ajustar Recursos do Sidecar

```yaml
# Em IstioOperator
values:
  global:
    proxy:
      resources:
        requests:
          cpu: 100m
          memory: 128Mi
        limits:
          cpu: 500m
          memory: 256Mi
```

#### Otimizar Access Logging

```yaml
# Desabilitar access log em produção se não necessário
meshConfig:
  accessLogFile: ""  # Desabilita
```

---

## Comandos Úteis

```bash
# Restart de todos os sidecars
kubectl rollout restart deployment -n my-api

# Verificar versão do proxy
istioctl proxy-status

# Dump completo de configuração
istioctl proxy-config all <pod-name> -n my-api -o json > proxy-config.json

# Verificar métricas Prometheus
kubectl port-forward -n istio-system svc/prometheus 9090:9090
# Abrir http://localhost:9090

# Dashboard Kiali
kubectl port-forward -n istio-system svc/kiali 20001:20001
# Abrir http://localhost:20001
```

---

## Referências

- [Istio Troubleshooting](https://istio.io/latest/docs/ops/common-problems/)
- [Debugging Envoy](https://istio.io/latest/docs/ops/diagnostic-tools/proxy-cmd/)
- [Traffic Management](https://istio.io/latest/docs/concepts/traffic-management/)
- [Security](https://istio.io/latest/docs/concepts/security/)

---

**Last Updated**: 2025-12-04
**Maintainer**: Platform Engineering Team
