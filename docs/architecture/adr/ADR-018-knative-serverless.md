# ADR-018: Knative Serverless Support

## Status

Accepted

## Context

O projeto Python API Base já suporta múltiplas opções de deployment:
- Docker Compose para desenvolvimento local
- Kubernetes com Helm charts
- ArgoCD para GitOps
- Istio para service mesh
- AWS Lambda e Vercel para serverless FaaS

No entanto, faltava uma opção serverless nativa para Kubernetes que oferecesse:
- Auto-scaling com scale-to-zero para otimização de custos
- Traffic management nativo para canary deployments
- Event-driven architecture integrada
- Portabilidade sem vendor lock-in

## Decision

Adicionamos suporte ao Knative 1.15 como plataforma serverless para Kubernetes, incluindo:

1. **Knative Serving**: Deploy de aplicações serverless com auto-scaling
2. **Knative Eventing**: Event-driven architecture com CloudEvents
3. **Integração com Istio**: Aproveitando a infraestrutura de service mesh existente
4. **Integração com ArgoCD**: GitOps para Knative Services
5. **Python CloudEvents Adapter**: Biblioteca para processar eventos no FastAPI

### Componentes Implementados

```
deployments/knative/
├── base/                    # Knative Service base
├── overlays/                # Dev/Staging/Prod configs
├── eventing/                # Kafka, Broker, Triggers
└── traffic/                 # Canary, Blue-Green examples

src/infrastructure/eventing/
├── cloudevents/             # CloudEvents v1.0 adapter
└── knative/                 # Manifest generator/validator
```

### Configuração por Ambiente

| Ambiente | minScale | maxScale | Concurrency | Resources |
|----------|----------|----------|-------------|-----------|
| Dev | 0 | 3 | 50 | 50m-500m CPU, 128Mi-512Mi |
| Staging | 1 | 5 | 80 | 100m-750m CPU, 256Mi-768Mi |
| Prod | 2 | 20 | 100 | 200m-2000m CPU, 512Mi-2Gi |

## Consequences

### Positive

1. **Otimização de custos**: Scale-to-zero em ambientes de desenvolvimento
2. **Portabilidade**: Sem vendor lock-in, funciona em qualquer Kubernetes
3. **Traffic management**: Canary deployments nativos sem configuração adicional
4. **Event-driven**: Integração com Kafka existente via CloudEvents
5. **Observability**: Métricas e tracing integrados com Istio
6. **GitOps**: Deployment via ArgoCD como outros recursos

### Negative

1. **Complexidade**: Mais uma opção de deployment para manter
2. **Cold start**: Latência inicial quando scale-to-zero está ativo
3. **Dependências**: Requer Knative instalado no cluster
4. **Curva de aprendizado**: Conceitos específicos do Knative

### Neutral

1. **Coexistência**: Pode rodar junto com deployments tradicionais
2. **Migração gradual**: Não requer migração completa

## Alternatives Considered

### 1. KEDA (Kubernetes Event-driven Autoscaling)

- **Prós**: Mais leve, foco em autoscaling
- **Contras**: Não oferece traffic management, menos features serverless
- **Decisão**: Knative oferece solução mais completa

### 2. OpenFaaS

- **Prós**: Simples, boa documentação
- **Contras**: Menos integração com Istio, comunidade menor
- **Decisão**: Knative tem melhor integração com nosso stack

### 3. Apenas AWS Lambda

- **Prós**: Já implementado, maturidade
- **Contras**: Vendor lock-in, não funciona em outros clouds
- **Decisão**: Manter Lambda como opção, adicionar Knative para portabilidade

## References

- [Knative Documentation](https://knative.dev/docs/)
- [CloudEvents Specification](https://cloudevents.io/)
- [Knative + Istio Integration](https://knative.dev/docs/install/installing-istio/)
- [ADR-016: Istio Service Mesh](./ADR-016-istio-service-mesh.md)
- [ADR-015: GitOps ArgoCD](./ADR-015-gitops-argocd.md)

## Date

2025-12-05

## Authors

- Platform Team
