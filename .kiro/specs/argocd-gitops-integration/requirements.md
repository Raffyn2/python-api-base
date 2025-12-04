# Requirements Document

## Introduction

Este documento especifica os requisitos para integração de ArgoCD e práticas GitOps ao projeto Python API Base. O objetivo é implementar um fluxo de deployment declarativo, automatizado e auditável, onde o estado desejado da infraestrutura é definido em Git e sincronizado automaticamente com os clusters Kubernetes.

A integração complementa a infraestrutura existente (Helm charts, K8s manifests, Terraform) adicionando uma camada de continuous delivery GitOps-native que garante consistência entre ambientes e facilita rollbacks.

## Glossary

- **ArgoCD**: Ferramenta declarativa de GitOps continuous delivery para Kubernetes
- **GitOps**: Metodologia onde Git é a única fonte de verdade para infraestrutura declarativa
- **Application**: Recurso ArgoCD que define uma aplicação a ser sincronizada
- **ApplicationSet**: Recurso ArgoCD para gerenciar múltiplas Applications de forma dinâmica
- **AppProject**: Recurso ArgoCD que agrupa Applications com políticas de segurança
- **Sync Policy**: Configuração que define como e quando ArgoCD sincroniza recursos
- **Health Check**: Verificação de saúde customizada para recursos Kubernetes
- **Sync Wave**: Mecanismo para ordenar a sincronização de recursos
- **Helm Values Generator**: Plugin ArgoCD para gerar values dinamicamente
- **Image Updater**: Componente ArgoCD para atualização automática de imagens
- **Kustomize**: Ferramenta de customização de manifests Kubernetes
- **Sealed Secrets**: Mecanismo para criptografar secrets em Git

## Requirements

### Requirement 1

**User Story:** As a DevOps engineer, I want to deploy ArgoCD configuration manifests, so that I can manage application deployments declaratively through Git.

#### Acceptance Criteria

1. WHEN the ArgoCD manifests are applied to a cluster THEN the system SHALL create a functional ArgoCD installation with all required CRDs
2. WHEN ArgoCD is installed THEN the system SHALL configure RBAC with least-privilege access for service accounts
3. WHEN ArgoCD is deployed THEN the system SHALL expose the UI through an Ingress with TLS termination
4. WHEN ArgoCD starts THEN the system SHALL connect to the configured Git repository using SSH key authentication
5. IF ArgoCD installation fails THEN the system SHALL provide clear error messages indicating the failure reason

### Requirement 2

**User Story:** As a DevOps engineer, I want to define Application resources for each environment, so that I can manage multi-environment deployments from a single Git repository.

#### Acceptance Criteria

1. WHEN an Application resource is created THEN the system SHALL reference the correct Helm chart path and values file for the target environment
2. WHEN an Application targets development environment THEN the system SHALL use auto-sync with self-heal enabled
3. WHEN an Application targets production environment THEN the system SHALL require manual sync approval
4. WHEN an Application is synced THEN the system SHALL apply resources in the correct order using sync waves
5. WHEN an Application sync fails THEN the system SHALL trigger configured notification channels

### Requirement 3

**User Story:** As a DevOps engineer, I want to use ApplicationSets for dynamic application generation, so that I can reduce configuration duplication across environments.

#### Acceptance Criteria

1. WHEN an ApplicationSet is defined with a list generator THEN the system SHALL create one Application per environment entry
2. WHEN an ApplicationSet uses a Git generator THEN the system SHALL discover and create Applications based on directory structure
3. WHEN a new environment directory is added to Git THEN the system SHALL automatically create the corresponding Application
4. WHEN an environment directory is removed from Git THEN the system SHALL delete the corresponding Application
5. WHEN ApplicationSet parameters change THEN the system SHALL update all generated Applications accordingly

### Requirement 4

**User Story:** As a DevOps engineer, I want to configure AppProjects with security policies, so that I can enforce access control and resource restrictions.

#### Acceptance Criteria

1. WHEN an AppProject is created THEN the system SHALL define allowed source repositories and destination clusters
2. WHEN an AppProject is configured THEN the system SHALL restrict deployable resource kinds to prevent privilege escalation
3. WHEN a user attempts to deploy outside allowed namespaces THEN the system SHALL reject the sync operation
4. WHEN an AppProject defines role bindings THEN the system SHALL enforce RBAC for Application management
5. WHEN cluster-scoped resources are deployed THEN the system SHALL require explicit AppProject permission

### Requirement 5

**User Story:** As a DevOps engineer, I want to integrate ArgoCD Image Updater, so that I can automatically update container images when new versions are pushed.

#### Acceptance Criteria

1. WHEN a new image tag is pushed to the registry THEN the system SHALL detect the update within the configured polling interval
2. WHEN Image Updater detects a new image THEN the system SHALL update the Application with the new tag following the configured strategy
3. WHEN Image Updater updates an image THEN the system SHALL commit the change back to Git maintaining GitOps principles
4. WHEN multiple update strategies are configured THEN the system SHALL apply the correct strategy per Application annotation
5. IF image registry is unreachable THEN the system SHALL retry with exponential backoff and log the failure

### Requirement 6

**User Story:** As a DevOps engineer, I want to configure notifications for sync events, so that I can monitor deployment status across environments.

#### Acceptance Criteria

1. WHEN an Application sync succeeds THEN the system SHALL send a notification to the configured Slack channel
2. WHEN an Application sync fails THEN the system SHALL send an alert with error details to the configured channels
3. WHEN an Application health degrades THEN the system SHALL trigger a warning notification
4. WHEN notifications are configured THEN the system SHALL support multiple channels including Slack, email, and webhooks
5. WHEN notification templates are defined THEN the system SHALL render messages with Application context variables

### Requirement 7

**User Story:** As a DevOps engineer, I want to implement custom health checks for application resources, so that ArgoCD can accurately report application health status.

#### Acceptance Criteria

1. WHEN a custom health check is defined THEN the system SHALL evaluate resource health using the specified Lua script
2. WHEN a Deployment has all replicas ready THEN the system SHALL report health status as Healthy
3. WHEN a Job completes successfully THEN the system SHALL report health status as Healthy
4. WHEN a resource health check fails THEN the system SHALL report the specific failure reason
5. WHEN health checks are configured THEN the system SHALL support custom resource types beyond built-in Kubernetes resources

### Requirement 8

**User Story:** As a DevOps engineer, I want to configure sync waves and hooks, so that I can control the order of resource deployment and execute pre/post-sync operations.

#### Acceptance Criteria

1. WHEN resources have sync wave annotations THEN the system SHALL deploy resources in ascending wave order
2. WHEN a PreSync hook is defined THEN the system SHALL execute it before the main sync operation
3. WHEN a PostSync hook is defined THEN the system SHALL execute it after successful sync completion
4. WHEN a SyncFail hook is defined THEN the system SHALL execute it when sync fails
5. IF a hook fails THEN the system SHALL halt the sync process and report the failure

### Requirement 9

**User Story:** As a DevOps engineer, I want to integrate Sealed Secrets for secret management, so that I can safely store encrypted secrets in Git.

#### Acceptance Criteria

1. WHEN a SealedSecret resource is applied THEN the system SHALL decrypt it using the cluster's private key
2. WHEN a SealedSecret is synced THEN the system SHALL create the corresponding Kubernetes Secret
3. WHEN the Sealed Secrets controller is deployed THEN the system SHALL generate and store the encryption key pair
4. WHEN secrets need rotation THEN the system SHALL support re-encryption with new keys
5. IF decryption fails THEN the system SHALL log the error and mark the resource as degraded

### Requirement 10

**User Story:** As a developer, I want comprehensive documentation for the GitOps workflow, so that I can understand and follow the deployment process.

#### Acceptance Criteria

1. WHEN documentation is created THEN the system SHALL include a getting started guide with prerequisites
2. WHEN documentation is created THEN the system SHALL provide step-by-step instructions for common operations
3. WHEN documentation is created THEN the system SHALL include architecture diagrams showing the GitOps flow
4. WHEN documentation is created THEN the system SHALL document troubleshooting procedures for common issues
5. WHEN documentation is created THEN the system SHALL include ADR explaining the GitOps architecture decisions

