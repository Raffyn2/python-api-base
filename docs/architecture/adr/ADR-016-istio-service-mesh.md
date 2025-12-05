# ADR-016: Istio Service Mesh Integration

## Status

Accepted

## Context

O projeto Python API Base necessita de capacidades avançadas de:

1. **Traffic Management**: Canary deployments, circuit breakers, retries
2. **Security**: mTLS automático, authorization policies, JWT validation
3. **Observability**: Distributed tracing, métricas detalhadas, access logs

A infraestrutura atual com Kubernetes, Helm e ArgoCD não fornece essas capacidades nativamente.

### Problema

- Comunicação entre serviços não é criptografada por padrão
- Não há circuit breakers ou retry policies automáticos
- Canary deployments requerem configuração manual complexa
- Observabilidade limitada a métricas de aplicação

## Decision

Adotar **Istio Service Mesh** como solução de service mesh para o projeto.

### Alternativas Consideradas

| Solução | Prós | Contras |
|---------|------|---------|
| **Istio** | Feature-rich, mTLS automático, grande comunidade | Complexidade, overhead de recursos |
| Linkerd | Leve, simples, baixo overhead | Menos features, menor comunidade |
| Consul Connect | Integração HashiCorp, multi-cloud | Vendor lock-in, complexidade |
| AWS App Mesh | Integração AWS nativa | Vendor lock-in, apenas AWS |
| Cilium | eBPF-based, alta performance | Requer kernel recente, menos maduro |

### Justificativa

1. **Maturidade**: Istio é o service mesh mais maduro e amplamente adotado
2. **Features**: Conjunto completo de traffic management, security e observability
3. **Comunidade**: Grande comunidade, documentação extensa, suporte enterprise
4. **Integração**: Excelente integração com Kubernetes, Prometheus, Jaeger
5. **GitOps**: Recursos declarativos compatíveis com ArgoCD

## Consequences

### Positivas

1. **mTLS Automático**: Criptografia e autenticação entre todos os serviços
2. **Traffic Management**: Canary, blue-green, A/B testing nativos
3. **Resiliência**: Circuit breakers, retries, timeouts configuráveis
4. **Observabilidade**: Métricas, traces e logs detalhados sem código
5. **Security**: Authorization policies baseadas em identidade
6. **Zero Trust**: Modelo de segurança zero trust implementado

### Negativas

1. **Complexidade**: Curva de aprendizado significativa
2. **Overhead**: ~50-100MB RAM por sidecar, latência adicional (~1-3ms)
3. **Debugging**: Troubleshooting mais complexo com proxies
4. **Recursos**: Istiod requer recursos significativos (512Mi-2Gi RAM)

### Neutras

1. **Migração**: Sidecar injection pode ser gradual por namespace
2. **Compatibilidade**: Requer Kubernetes 1.25+

## Implementation

### Estrutura de Arquivos

```
deployments/istio/
├── base/
│   ├── istio-operator.yaml
│   ├── gateway.yaml
│   ├── virtualservice.yaml
│   ├── destinationrule.yaml
│   ├── peerauthentication.yaml
│   ├── authorizationpolicy.yaml
│   └── serviceentry.yaml
└── overlays/
    ├── dev/
    ├── staging/
    └── prod/
```

### Configuração por Ambiente

| Configuração | Dev | Staging | Prod |
|--------------|-----|---------|------|
| mTLS Mode | PERMISSIVE | STRICT | STRICT |
| Egress Policy | ALLOW_ANY | REGISTRY_ONLY | REGISTRY_ONLY |
| Tracing Sampling | 10% | 5% | 1% |
| Istiod Replicas | 1 | 2 | 3 |

### Integração ArgoCD

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: istio-system
spec:
  source:
    path: deployments/istio/overlays/prod
  syncPolicy:
    automated:
      prune: false  # Manual para Istio
```

## Risks

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Overhead de latência | Média | Baixo | Monitorar P99, otimizar config |
| Complexidade operacional | Alta | Médio | Documentação, runbooks, treinamento |
| Falha do control plane | Baixa | Alto | HA com múltiplas réplicas |
| Incompatibilidade de versão | Média | Médio | Testar upgrades em staging |

## Metrics

### KPIs de Sucesso

1. **mTLS Coverage**: 100% dos serviços com mTLS STRICT
2. **Latência P99**: < 5ms overhead adicionado
3. **Disponibilidade**: 99.9% uptime do control plane
4. **Incident Response**: Redução de 50% no MTTR com observabilidade

### Monitoramento

- Dashboard Grafana para métricas Istio
- Alertas para circuit breaker opens
- Alertas para mTLS failures
- Kiali para visualização de topologia

## References

- [Istio Documentation](https://istio.io/latest/docs/)
- [Istio Best Practices](https://istio.io/latest/docs/ops/best-practices/)
- [CNCF Service Mesh Comparison](https://landscape.cncf.io/card-mode?category=service-mesh)
- [Design Document](.kiro/specs/istio-service-mesh/design.md)

## Decision Date

2025-12-04

## Decision Makers

- Platform Engineering Team
- Security Team
- Architecture Review Board
