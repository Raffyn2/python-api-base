# ADR-021: Deployments Validation Framework

**Status:** Accepted
**Date:** 2025-12-05
**Author:** Code Review Automation
**Category:** Infrastructure, Testing

## Contexto

Após o code review completo da pasta `deployments/` (ADR-020), identificamos a necessidade de um framework de validação automatizada para garantir que todas as configurações de infraestrutura sigam as melhores práticas de segurança e padrões organizacionais.

## Decisão

Implementar um framework de validação baseado em property-based testing usando Hypothesis, com validadores específicos para cada tecnologia de deployment.

## Arquitetura do Framework

```
tests/properties/deployments/
├── __init__.py
├── validators.py              # Classes de validação
└── test_manifest_properties.py # Property tests
```

### Componentes

1. **K8sManifestValidator**: Valida manifests Kubernetes
   - Security contexts (seccompProfile, runAsNonRoot, capabilities)
   - Network policies
   - Resource limits
   - Labels convention
   - Health probes

2. **HelmChartValidator**: Valida Helm charts
   - Values validation
   - No 'latest' tags
   - External secrets configuration
   - Chart.yaml requirements

3. **TerraformValidator**: Valida configurações Terraform
   - Backend encryption
   - State locking
   - Sensitive variables
   - Provider versions

4. **DockerComposeValidator**: Valida Docker Compose
   - Security options
   - Health checks
   - Resource limits

5. **IstioValidator**: Valida configurações Istio
   - mTLS configuration
   - Authorization policies
   - Rate limiting

6. **KnativeValidator**: Valida configurações Knative
   - Autoscaling annotations
   - Security context

## Properties Implementadas

### Segurança (12 properties)
- Property 1: Security Context Completeness
- Property 2: Network Policy Existence
- Property 11: Istio mTLS Strict
- Property 12: Authorization Deny-All
- Property 13: Rate Limiting Configured
- Property 15: Knative Security Context
- Property 16: Docker Multi-Stage Build
- Property 17: Docker Non-Root
- Property 37: Sealed Secrets Usage
- Property 38: Labels Convention
- Property 42: EmptyDir Size Limits
- Property 43: Service Account Token Disabled

### Recursos (6 properties)
- Property 3: Resource Limits Defined
- Property 23: Resource Quota Exists
- Property 29: Docker Resource Limits
- Property 35: Single NAT Gateway Option
- Property 44: Revision History Limit
- Property 45: Rolling Update Strategy

### GitOps (5 properties)
- Property 4: No Latest Tags
- Property 5: External Secrets Enabled
- Property 9: ArgoCD Sync Waves
- Property 10: Production Manual Sync
- Property 25: ArgoCD Image Updater Configured

### Terraform (4 properties)
- Property 6: Terraform Backend Encryption
- Property 7: Sensitive Variables Marked
- Property 8: Common Tags Applied
- Property 24: Terraform Provider Versions Constrained

### Observabilidade (6 properties)
- Property 18: ServiceMonitor Exists
- Property 19: Alert Severity Labels
- Property 32: Tracing Sampling Configured
- Property 39: Annotations for Prometheus
- Property 30: Docker Health Checks
- Property 31: Structured Logging Enabled

### Alta Disponibilidade (8 properties)
- Property 20: Topology Spread Constraints
- Property 21: PDB Configured
- Property 22: HPA Behavior Policies
- Property 33: Liveness Probe Configured
- Property 34: Readiness Probe Configured
- Property 40: Graceful Shutdown
- Property 41: DNS Config Optimized
- Property 28: Knative Autoscaling Metrics

### Knative/Serverless (3 properties)
- Property 14: Knative Scale-to-Zero
- Property 26: Istio JWT Validation
- Property 27: Istio Egress Restricted

## Integração CI/CD

### Script de Validação

```bash
./scripts/validate-manifests.sh [--fix] [--verbose]
```

O script executa:
1. YAML lint
2. Helm lint
3. Kubernetes manifest validation (kubeconform/kubeval)
4. Terraform format/validate
5. Kustomize build
6. Security scanning (checkov/trivy)
7. Property-based tests

### GitHub Actions

```yaml
# .github/workflows/validate-deployments.yml
name: Validate Deployments

on:
  pull_request:
    paths:
      - 'deployments/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run validation
        run: ./scripts/validate-manifests.sh
```

## Helm Values Schema

Adicionado `values.schema.json` para validação de valores Helm:

- Validação de tipos
- Constraints de segurança (runAsNonRoot: true, etc.)
- Rejeição de 'latest' tag
- Requisitos de resources

## Consequências

### Positivas
- Validação automatizada em CI/CD
- Detecção precoce de problemas de segurança
- Documentação viva das regras de validação
- Conformidade com CIS benchmarks
- Redução de erros em produção

### Negativas
- Overhead de manutenção dos validadores
- Possíveis falsos positivos
- Necessidade de atualização com novas versões de K8s/Helm

## Ferramentas Recomendadas

| Ferramenta | Propósito | Instalação |
|------------|-----------|------------|
| yamllint | YAML syntax | `pip install yamllint` |
| helm | Chart validation | `brew install helm` |
| kubeconform | K8s schema | `brew install kubeconform` |
| checkov | Security scan | `pip install checkov` |
| trivy | Vulnerability scan | `brew install trivy` |
| pytest | Property tests | `pip install pytest hypothesis` |

## Referências

- [ADR-020: Deployments Code Review](./ADR-020-deployments-code-review.md)
- [Kubernetes Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Helm Best Practices](https://helm.sh/docs/chart_best_practices/)
- [Property-Based Testing with Hypothesis](https://hypothesis.readthedocs.io/)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)
