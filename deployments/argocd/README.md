# ArgoCD GitOps Integration

Configuração GitOps para Python API Base usando ArgoCD como ferramenta de continuous delivery.

## Visão Geral

Este módulo implementa práticas GitOps onde Git é a única fonte de verdade para o estado desejado da infraestrutura. ArgoCD sincroniza automaticamente o estado do cluster Kubernetes com as definições declarativas no repositório.

## Pré-requisitos

| Componente | Versão | Descrição |
|------------|--------|-----------|
| Kubernetes | 1.28+ | Cluster de destino |
| kubectl | 1.28+ | CLI Kubernetes |
| Helm | 3.14+ | Package manager |
| kubeseal | 0.24+ | Sealed Secrets CLI |
| ArgoCD CLI | 2.13+ | (Opcional) CLI ArgoCD |

## Quick Start

### 1. Instalar ArgoCD

```bash
# Criar namespace e aplicar manifests base
kubectl apply -k deployments/argocd/overlays/dev

# Aguardar pods ficarem prontos
kubectl wait --for=condition=Ready pods -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s

# Obter senha inicial do admin
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### 2. Acessar UI

```bash
# Port-forward para acesso local
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Acessar: https://localhost:8080
# Usuário: admin
# Senha: (obtida no passo anterior)
```

### 3. Configurar Repositório

```bash
# Via CLI
argocd login localhost:8080 --insecure
argocd repo add https://github.com/org/python-api-base.git --ssh-private-key-path ~/.ssh/id_rsa

# Ou via UI: Settings > Repositories > Connect Repo
```

### 4. Aplicar Applications

```bash
# Aplicar AppProjects
kubectl apply -k deployments/argocd/projects

# Aplicar Applications
kubectl apply -k deployments/argocd/applications
```

## Estrutura de Diretórios

```
argocd/
├── base/                    # Instalação base do ArgoCD
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── argocd-cm.yaml       # ConfigMap principal
│   ├── argocd-rbac-cm.yaml  # RBAC policies
│   └── ingress.yaml         # Ingress para UI
│
├── projects/                # AppProjects
│   ├── python-api-base.yaml # Projeto principal
│   └── infrastructure.yaml  # Projeto de infra
│
├── applications/            # Application definitions
│   ├── dev/
│   ├── staging/
│   └── prod/
│
├── applicationsets/         # ApplicationSets
│   └── python-api-base-set.yaml
│
├── notifications/           # Notificações
│   ├── argocd-notifications-cm.yaml
│   └── argocd-notifications-secret.yaml
│
├── image-updater/           # Image Updater
│   └── argocd-image-updater-config.yaml
│
├── hooks/                   # Sync hooks
│   ├── presync-migration.yaml
│   └── postsync-smoke-test.yaml
│
├── sealed-secrets/          # Sealed Secrets
│   ├── sealed-secrets-controller.yaml
│   └── sealedsecret-templates.yaml
│
└── overlays/                # Environment overlays
    ├── dev/
    ├── staging/
    └── prod/
```

## Ambientes

### Development

- Auto-sync habilitado
- Self-heal habilitado
- Prune habilitado
- Image tags: `v*.*.*-dev.*`

```bash
kubectl apply -k deployments/argocd/overlays/dev
```

### Staging

- Auto-sync habilitado
- Self-heal desabilitado
- Prune habilitado
- Image tags: `v*.*.*-rc.*`

```bash
kubectl apply -k deployments/argocd/overlays/staging
```

### Production

- Sync manual obrigatório
- Self-heal desabilitado
- Prune desabilitado
- Image tags: `v*.*.*` (releases apenas)
- Sync windows configuradas (horário comercial)

```bash
kubectl apply -k deployments/argocd/overlays/prod
```

## Operações Comuns

### Sync Manual

```bash
# Via CLI
argocd app sync python-api-base-prod

# Via kubectl
kubectl patch application python-api-base-prod -n argocd \
  --type merge -p '{"operation":{"sync":{"revision":"HEAD"}}}'
```

### Rollback

```bash
# Via CLI - rollback para revisão específica
argocd app rollback python-api-base-prod <revision>

# Via Git (preferido - mantém GitOps)
git revert <commit-sha>
git push origin main
# ArgoCD sincroniza automaticamente
```

### Verificar Status

```bash
# Status de todas as apps
argocd app list

# Status detalhado
argocd app get python-api-base-prod

# Health check
argocd app health python-api-base-prod
```

### Diff (Preview)

```bash
# Ver diferenças antes de sync
argocd app diff python-api-base-prod

# Dry-run
argocd app sync python-api-base-prod --dry-run
```

## Sealed Secrets

### Criar Secret Selado

```bash
# 1. Criar secret normal
kubectl create secret generic my-secret \
  --from-literal=password=mysecretpassword \
  --dry-run=client -o yaml > my-secret.yaml

# 2. Selar o secret
kubeseal --format yaml < my-secret.yaml > my-sealedsecret.yaml

# 3. Aplicar (ou commitar no Git)
kubectl apply -f my-sealedsecret.yaml
```

### Rotação de Chaves

```bash
# Verificar chave atual
kubeseal --fetch-cert --controller-name=sealed-secrets-controller \
  --controller-namespace=sealed-secrets > sealed-secrets.pem

# Re-selar secrets após rotação
kubeseal --re-encrypt < old-sealedsecret.yaml > new-sealedsecret.yaml
```

## Notificações

### Configurar Slack

1. Criar Slack App e obter Bot Token
2. Atualizar secret:

```bash
kubectl create secret generic argocd-notifications-secret \
  --from-literal=slack-token=xoxb-your-token \
  -n argocd --dry-run=client -o yaml | kubectl apply -f -
```

3. Adicionar anotação na Application:

```yaml
annotations:
  notifications.argoproj.io/subscribe.on-sync-succeeded.slack: my-channel
```

### Canais Configurados

| Trigger | Canal Dev | Canal Staging | Canal Prod |
|---------|-----------|---------------|------------|
| sync-succeeded | dev-deployments | staging-deployments | prod-deployments |
| sync-failed | dev-alerts | staging-alerts | prod-alerts |
| health-degraded | dev-alerts | staging-alerts | prod-alerts |

## Image Updater

### Estratégias de Atualização

| Estratégia | Descrição | Uso |
|------------|-----------|-----|
| semver | Segue versionamento semântico | Produção |
| latest | Sempre última tag | Dev |
| digest | Atualiza por digest | Imutabilidade |
| name | Ordenação alfabética | Casos especiais |

### Configurar Atualização Automática

```yaml
metadata:
  annotations:
    argocd-image-updater.argoproj.io/image-list: api=ghcr.io/org/python-api-base
    argocd-image-updater.argoproj.io/api.update-strategy: semver
    argocd-image-updater.argoproj.io/api.allow-tags: regexp:^v[0-9]+\.[0-9]+\.[0-9]+$
    argocd-image-updater.argoproj.io/write-back-method: git
```

## Troubleshooting

### Application não sincroniza

```bash
# Verificar eventos
kubectl describe application python-api-base-dev -n argocd

# Verificar logs do controller
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller

# Forçar refresh
argocd app get python-api-base-dev --refresh
```

### Sealed Secret não decripta

```bash
# Verificar controller
kubectl logs -n sealed-secrets -l app.kubernetes.io/name=sealed-secrets-controller

# Verificar se secret foi criado
kubectl get secrets -n python-api-prod

# Re-selar com certificado correto
kubeseal --fetch-cert > cert.pem
kubeseal --cert cert.pem < secret.yaml > sealedsecret.yaml
```

### Image Updater não atualiza

```bash
# Verificar logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-image-updater

# Verificar anotações
kubectl get application python-api-base-dev -n argocd -o yaml | grep -A10 annotations

# Testar acesso ao registry
argocd-image-updater test ghcr.io/org/python-api-base
```

### Notificações não chegam

```bash
# Verificar secret
kubectl get secret argocd-notifications-secret -n argocd -o yaml

# Verificar ConfigMap
kubectl get cm argocd-notifications-cm -n argocd -o yaml

# Testar template
argocd-notifications template notify app-sync-succeeded python-api-base-dev
```

## Validação

```bash
# Validar manifests
make validate-argocd

# Executar property tests
pytest tests/properties/test_argocd_manifests.py -v

# Lint YAML
yamllint deployments/argocd/

# Validar schemas Kubernetes
kubeval deployments/argocd/base/*.yaml
```

## Referências

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [ArgoCD Image Updater](https://argocd-image-updater.readthedocs.io/)
- [Sealed Secrets](https://sealed-secrets.netlify.app/)
- [ADR-015: GitOps Architecture](../../docs/architecture/adr/ADR-015-gitops-argocd.md)
