# ADR-002: GitHub Actions Security Hardening

## Status

Accepted

## Date

2024-12-05

## Context

O projeto utiliza GitHub Actions para CI/CD. A configuração original apresentava vulnerabilidades de segurança conhecidas:

1. Actions referenciadas por tags mutáveis (v4, v5) ao invés de SHA commits
2. Permissões excessivas em workflows
3. Falta de políticas de segurança documentadas
4. Ausência de CODEOWNERS para controle de aprovações
5. Dependabot configurado apenas para version updates

### Riscos Identificados

- **Supply Chain Attack**: Tags podem ser movidas para commits maliciosos
- **Privilege Escalation**: Tokens com permissões excessivas podem ser explorados
- **Unauthorized Changes**: Sem CODEOWNERS, mudanças críticas podem passar sem revisão adequada

## Decision

Implementar hardening completo seguindo as melhores práticas de segurança:

### 1. SHA Pinning para Actions

Todas as GitHub Actions são referenciadas por SHA completo (40 caracteres):

```yaml
# Antes (vulnerável)
uses: actions/checkout@v4

# Depois (seguro)
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

### 2. Least Privilege Permissions

Permissões definidas no nível global como vazias e concedidas apenas onde necessário:

```yaml
permissions: {}

jobs:
  build:
    permissions:
      contents: read
```

### 3. Security Scanning Pipeline

- **SAST**: Bandit, CodeQL
- **SCA**: Trivy, Dependabot
- **Secrets**: TruffleHog, Gitleaks
- **Container**: Trivy image scanning
- **IaC**: Trivy, Checkov para Terraform/Helm
- **SBOM**: SPDX e CycloneDX

### 4. CODEOWNERS

Arquivo definindo ownership por área:
- `/src/` - backend-team
- `/deployments/` - platform-team
- `/.github/workflows/` - security-team

### 5. Security Policy

SECURITY.md com:
- Processo de disclosure responsável
- SLA por severidade CVSS
- Canais de comunicação

## Consequences

### Positive

- Proteção contra supply chain attacks
- Auditoria clara de permissões
- Revisão obrigatória por especialistas
- Compliance com OSSF Scorecard
- Rastreabilidade de vulnerabilidades

### Negative

- Manutenção adicional para atualizar SHAs
- Dependabot não atualiza SHAs automaticamente (requer renovate ou manual)
- Processo de PR mais rigoroso pode aumentar tempo de merge

### Neutral

- Curva de aprendizado para novos contribuidores
- Necessidade de documentação adicional

## Alternatives Considered

### 1. Manter Tags com Dependabot

**Rejeitado**: Não protege contra tag hijacking entre atualizações do Dependabot.

### 2. Usar apenas Actions oficiais (actions/*)

**Rejeitado**: Limita funcionalidades necessárias (Trivy, Helm, etc).

### 3. Self-hosted runners

**Considerado para futuro**: Adiciona controle mas aumenta complexidade operacional.

## Compliance

- OSSF Scorecard: Token-Permissions, Pinned-Dependencies
- SLSA Level 2: Provenance attestation
- SOC 2: Audit trail, access control

## References

- [GitHub Actions Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [OSSF Scorecard](https://securityscorecards.dev/)
- [StepSecurity Harden Runner](https://www.stepsecurity.io/)
- [OpenSSF Best Practices](https://openssf.org/blog/2024/08/12/mitigating-attack-vectors-in-github-workflows/)
