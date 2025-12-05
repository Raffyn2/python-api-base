# ArgoCD Troubleshooting Guide

Guia de resolução de problemas comuns com ArgoCD e GitOps.

## Diagnóstico Rápido

```bash
# Status geral
argocd app list

# Health de uma app
argocd app get <app-name>

# Logs do ArgoCD
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server --tail=100
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller --tail=100
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server --tail=100
```

## Problemas Comuns

### 1. Application Stuck in "Progressing"

**Sintomas:**
- Status mostra "Progressing" por muito tempo
- Pods não ficam Ready

**Diagnóstico:**
```bash
# Ver recursos com problema
argocd app resources <app-name> --health-status Progressing

# Ver eventos do pod
kubectl describe pod -n <namespace> <pod-name>

# Ver logs do pod
kubectl logs -n <namespace> <pod-name>
```

**Causas Comuns:**
1. Image pull error
2. Resource limits insuficientes
3. Probes falhando
4. Dependências não disponíveis

**Soluções:**
```bash
# Image pull error - verificar secret
kubectl get secret -n <namespace> | grep pull
kubectl describe secret <pull-secret> -n <namespace>

# Resource limits - verificar quotas
kubectl describe resourcequota -n <namespace>

# Probes - verificar endpoints
kubectl exec -n <namespace> <pod-name> -- curl localhost:8000/health/live
```

### 2. Sync Failed

**Sintomas:**
- Status "Sync Failed"
- Erro no sync operation

**Diagnóstico:**
```bash
# Ver detalhes do erro
argocd app get <app-name>

# Ver operation state
kubectl get application <app-name> -n argocd -o jsonpath='{.status.operationState}'
```

**Causas Comuns:**
1. Manifest inválido
2. RBAC insuficiente
3. Resource conflict
4. Webhook validation failed

**Soluções:**
```bash
# Validar manifests localmente
helm template deployments/helm/api -f values.yaml | kubectl apply --dry-run=client -f -

# Verificar RBAC
kubectl auth can-i create deployments -n <namespace> --as system:serviceaccount:argocd:argocd-application-controller

# Forçar sync (cuidado!)
argocd app sync <app-name> --force
```

### 3. OutOfSync mas Sync não Resolve

**Sintomas:**
- App mostra OutOfSync
- Sync completa mas volta a OutOfSync

**Diagnóstico:**
```bash
# Ver diff detalhado
argocd app diff <app-name>

# Ver recursos ignorados
argocd app get <app-name> -o yaml | grep -A20 ignoreDifferences
```

**Causas Comuns:**
1. Controller modificando recursos (HPA, VPA)
2. Admission webhooks modificando specs
3. Campos calculados pelo Kubernetes

**Soluções:**
```yaml
# Adicionar ignoreDifferences na Application
spec:
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas
    - group: autoscaling
      kind: HorizontalPodAutoscaler
      jsonPointers:
        - /spec/minReplicas
```

### 4. Repository Connection Failed

**Sintomas:**
- Erro de conexão com Git
- "repository not accessible"

**Diagnóstico:**
```bash
# Verificar repositórios configurados
argocd repo list

# Testar conexão
argocd repo get <repo-url>

# Ver logs do repo-server
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server --tail=100
```

**Causas Comuns:**
1. SSH key inválida ou expirada
2. Token expirado
3. Firewall bloqueando
4. Rate limiting do GitHub

**Soluções:**
```bash
# Atualizar credenciais
argocd repo rm <repo-url>
argocd repo add <repo-url> --ssh-private-key-path ~/.ssh/id_rsa

# Verificar secret
kubectl get secret -n argocd -l argocd.argoproj.io/secret-type=repository
```

### 5. Image Updater não Atualiza

**Sintomas:**
- Nova imagem disponível mas não atualiza
- Nenhum commit do Image Updater

**Diagnóstico:**
```bash
# Ver logs do Image Updater
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-image-updater --tail=100

# Verificar anotações
kubectl get application <app-name> -n argocd -o yaml | grep -A10 "argocd-image-updater"

# Testar acesso ao registry
argocd-image-updater test <image>
```

**Causas Comuns:**
1. Anotações incorretas
2. Credenciais do registry inválidas
3. Tag pattern não match
4. Write-back method mal configurado

**Soluções:**
```bash
# Verificar credenciais do registry
kubectl get secret -n argocd | grep registry

# Verificar ConfigMap
kubectl get cm argocd-image-updater-config -n argocd -o yaml

# Forçar check
kubectl rollout restart deployment argocd-image-updater -n argocd
```

### 6. Sealed Secret não Decripta

**Sintomas:**
- SealedSecret aplicado mas Secret não criado
- Erro de decriptação

**Diagnóstico:**
```bash
# Ver logs do controller
kubectl logs -n sealed-secrets -l app.kubernetes.io/name=sealed-secrets-controller --tail=100

# Verificar SealedSecret
kubectl get sealedsecret -n <namespace>
kubectl describe sealedsecret <name> -n <namespace>
```

**Causas Comuns:**
1. Secret selado com chave diferente
2. Namespace incorreto no seal
3. Controller não está rodando
4. Chave rotacionada

**Soluções:**
```bash
# Verificar chave atual
kubeseal --fetch-cert --controller-name=sealed-secrets-controller \
  --controller-namespace=sealed-secrets > current-cert.pem

# Re-selar com chave correta
kubeseal --cert current-cert.pem < secret.yaml > sealedsecret.yaml

# Verificar se namespace está correto
kubeseal --namespace <correct-namespace> < secret.yaml > sealedsecret.yaml
```

### 7. Notificações não Chegam

**Sintomas:**
- Eventos ocorrem mas notificações não são enviadas
- Slack/Email não recebe mensagens

**Diagnóstico:**
```bash
# Ver logs do notifications controller
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-notifications-controller --tail=100

# Verificar ConfigMap
kubectl get cm argocd-notifications-cm -n argocd -o yaml

# Verificar Secret
kubectl get secret argocd-notifications-secret -n argocd
```

**Causas Comuns:**
1. Token inválido
2. Template com erro
3. Trigger não configurado
4. Anotação faltando na Application

**Soluções:**
```bash
# Testar notificação manualmente
argocd-notifications template notify <template-name> <app-name>

# Verificar anotações
kubectl get application <app-name> -n argocd -o yaml | grep notifications

# Atualizar token
kubectl create secret generic argocd-notifications-secret \
  --from-literal=slack-token=<new-token> \
  -n argocd --dry-run=client -o yaml | kubectl apply -f -
```

### 8. Sync Hook Falha

**Sintomas:**
- Sync para no hook
- Job do hook falha

**Diagnóstico:**
```bash
# Ver jobs do hook
kubectl get jobs -n <namespace> | grep -E "presync|postsync"

# Ver logs do job
kubectl logs -n <namespace> job/<hook-job-name>

# Ver eventos
kubectl describe job <hook-job-name> -n <namespace>
```

**Causas Comuns:**
1. Comando do hook falha
2. Timeout
3. Permissões insuficientes
4. Imagem não encontrada

**Soluções:**
```bash
# Verificar RBAC do ServiceAccount
kubectl auth can-i --list --as system:serviceaccount:<namespace>:<sa-name>

# Testar comando manualmente
kubectl run test-hook --image=<hook-image> --rm -it -- <command>

# Aumentar timeout
# Adicionar no hook: argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
```

## Comandos de Emergência

```bash
# Desabilitar auto-sync temporariamente
argocd app set <app-name> --sync-policy none

# Forçar sync ignorando erros
argocd app sync <app-name> --force --prune

# Deletar recursos órfãos
argocd app sync <app-name> --prune

# Hard refresh do cache
argocd app get <app-name> --hard-refresh

# Restart do ArgoCD
kubectl rollout restart deployment -n argocd argocd-server
kubectl rollout restart statefulset -n argocd argocd-application-controller
kubectl rollout restart deployment -n argocd argocd-repo-server
```

## Métricas para Monitoramento

```promql
# Sync failures
sum(argocd_app_sync_total{phase="Failed"}) by (name)

# Health status
argocd_app_info{health_status!="Healthy"}

# Sync duration
histogram_quantile(0.95, argocd_app_reconcile_bucket)

# Repository errors
argocd_git_request_total{request_type="fetch", grpc_code!="OK"}
```

## Referências

- [ArgoCD Troubleshooting](https://argo-cd.readthedocs.io/en/stable/operator-manual/troubleshooting/)
- [ArgoCD FAQ](https://argo-cd.readthedocs.io/en/stable/faq/)
- [Sealed Secrets Troubleshooting](https://sealed-secrets.netlify.app/troubleshooting/)
