# Requirements Document

## Introduction

Este documento especifica os requisitos para adicionar suporte ao Knative 1.15 ao Python API Base. Knative é uma plataforma serverless para Kubernetes que permite deploy de aplicações com auto-scaling (incluindo scale-to-zero), traffic management e eventing. A integração complementa a infraestrutura existente (Istio, ArgoCD, Helm) e oferece uma alternativa serverless nativa para Kubernetes, além das opções AWS Lambda e Vercel já existentes.

## Glossary

- **Knative**: Plataforma open-source que estende Kubernetes com componentes serverless
- **Knative Serving**: Componente responsável por deploy, auto-scaling e traffic management
- **Knative Eventing**: Componente para event-driven architectures e pub/sub
- **Knative Service (ksvc)**: Custom Resource que define uma aplicação serverless
- **Revision**: Snapshot imutável de código e configuração de um Knative Service
- **Configuration**: Define o estado desejado de um Knative Service
- **Route**: Gerencia traffic routing entre Revisions
- **Scale-to-Zero**: Capacidade de reduzir réplicas a zero quando não há tráfego
- **Concurrency**: Número de requests simultâneos por instância
- **Cold Start**: Tempo de inicialização quando uma instância é criada do zero
- **KPA (Knative Pod Autoscaler)**: Autoscaler padrão do Knative
- **HPA (Horizontal Pod Autoscaler)**: Autoscaler nativo do Kubernetes
- **Istio**: Service mesh já configurado no projeto para mTLS e traffic management
- **Kourier**: Networking layer alternativo ao Istio, mais leve

## Requirements

### Requirement 1

**User Story:** As a DevOps engineer, I want to deploy the Python API Base as a Knative Service, so that I can leverage serverless capabilities on Kubernetes with auto-scaling and scale-to-zero.

#### Acceptance Criteria

1. WHEN a user applies the Knative Service manifest THEN the system SHALL create a functional Knative Service with the Python API Base container
2. WHEN the Knative Service is created THEN the system SHALL configure health probes compatible with FastAPI endpoints (/health/live and /health/ready)
3. WHEN the Knative Service is deployed THEN the system SHALL expose the service via a publicly accessible URL through the Knative ingress
4. WHEN configuring the service THEN the system SHALL support environment variables injection from ConfigMaps and Secrets
5. WHEN the service manifest is parsed THEN the system SHALL validate it against the Knative Serving API v1 schema

### Requirement 2

**User Story:** As a platform engineer, I want to configure auto-scaling parameters for the Knative Service, so that I can optimize resource usage and cost while maintaining performance.

#### Acceptance Criteria

1. WHEN traffic drops to zero THEN the system SHALL scale the service to zero pods within the configured scale-down delay (default 30s)
2. WHEN traffic increases THEN the system SHALL scale up pods based on concurrency target (default 100 concurrent requests per pod)
3. WHEN configuring autoscaling THEN the system SHALL support both KPA (Knative Pod Autoscaler) and HPA (Horizontal Pod Autoscaler) classes
4. WHEN scaling occurs THEN the system SHALL respect minScale and maxScale boundaries defined in the configuration
5. WHEN the autoscaling configuration is serialized and deserialized THEN the system SHALL produce an equivalent configuration

### Requirement 3

**User Story:** As a release manager, I want to perform traffic splitting between revisions, so that I can implement canary deployments and gradual rollouts safely.

#### Acceptance Criteria

1. WHEN a new revision is deployed THEN the system SHALL support percentage-based traffic splitting between revisions
2. WHEN traffic splitting is configured THEN the system SHALL route traffic according to the specified percentages (sum equals 100%)
3. WHEN a revision is tagged THEN the system SHALL create a named URL for direct access to that specific revision
4. WHEN rollback is needed THEN the system SHALL support routing 100% traffic to a previous revision
5. WHEN traffic percentages are modified THEN the system SHALL validate that percentages sum to exactly 100

### Requirement 4

**User Story:** As a developer, I want Kustomize overlays for different environments, so that I can deploy the Knative Service with environment-specific configurations.

#### Acceptance Criteria

1. WHEN deploying to development THEN the system SHALL use development-specific settings (minScale=0, relaxed resources)
2. WHEN deploying to staging THEN the system SHALL use staging-specific settings (minScale=1, moderate resources)
3. WHEN deploying to production THEN the system SHALL use production-specific settings (minScale=2, strict resources, higher concurrency)
4. WHEN applying overlays THEN the system SHALL merge base configuration with environment patches correctly
5. WHEN overlay configuration is applied THEN the system SHALL produce valid Knative Service manifests

### Requirement 5

**User Story:** As a security engineer, I want the Knative Service to integrate with Istio service mesh, so that I can leverage mTLS, authorization policies and observability already configured in the project.

#### Acceptance Criteria

1. WHEN Istio is the networking layer THEN the system SHALL enable automatic sidecar injection for Knative pods
2. WHEN mTLS is enabled THEN the system SHALL encrypt all service-to-service communication
3. WHEN authorization policies exist THEN the system SHALL apply them to Knative Service traffic
4. WHEN the service is deployed THEN the system SHALL integrate with existing Istio VirtualServices and DestinationRules
5. WHEN Istio integration is configured THEN the system SHALL validate compatibility with Knative networking requirements

### Requirement 6

**User Story:** As a DevOps engineer, I want ArgoCD integration for GitOps deployment of Knative Services, so that I can maintain consistent deployment practices across all infrastructure.

#### Acceptance Criteria

1. WHEN ArgoCD syncs the repository THEN the system SHALL deploy Knative Services automatically
2. WHEN Knative resources change THEN the system SHALL detect drift and show sync status in ArgoCD
3. WHEN health checks are configured THEN ArgoCD SHALL correctly assess Knative Service health status
4. WHEN using ApplicationSets THEN the system SHALL support dynamic generation of Knative applications across environments
5. WHEN ArgoCD configuration is serialized THEN the system SHALL produce valid Application manifests

### Requirement 7

**User Story:** As a developer, I want comprehensive documentation for Knative deployment, so that I can understand and use the serverless capabilities effectively.

#### Acceptance Criteria

1. WHEN reading the documentation THEN the user SHALL find installation prerequisites and steps
2. WHEN reading the documentation THEN the user SHALL find configuration options with examples
3. WHEN reading the documentation THEN the user SHALL find troubleshooting guides for common issues
4. WHEN reading the documentation THEN the user SHALL find comparison with other serverless options (Lambda, Vercel)
5. WHEN the documentation is updated THEN the system SHALL maintain consistency with actual implementation

### Requirement 8

**User Story:** As a platform engineer, I want Knative Eventing integration, so that I can build event-driven architectures with the existing Kafka and RabbitMQ infrastructure.

#### Acceptance Criteria

1. WHEN Kafka events are produced THEN the system SHALL support KafkaSource to trigger Knative Services
2. WHEN using CloudEvents THEN the system SHALL format events according to CloudEvents specification v1.0
3. WHEN configuring event sources THEN the system SHALL support filtering events by type and source
4. WHEN events are received THEN the system SHALL route them to the appropriate Knative Service
5. WHEN CloudEvents are serialized and deserialized THEN the system SHALL preserve all required attributes

### Requirement 9

**User Story:** As a DevOps engineer, I want monitoring and observability for Knative Services, so that I can track performance, scaling events and troubleshoot issues.

#### Acceptance Criteria

1. WHEN the service is running THEN the system SHALL expose Prometheus metrics for request count, latency and error rate
2. WHEN scaling events occur THEN the system SHALL log scaling decisions with reasons
3. WHEN Grafana dashboards are configured THEN the system SHALL display Knative-specific metrics
4. WHEN alerts are configured THEN the system SHALL notify on cold start latency exceeding thresholds
5. WHEN metrics are collected THEN the system SHALL integrate with existing Prometheus ServiceMonitor configuration

### Requirement 10

**User Story:** As a developer, I want a Python adapter for CloudEvents, so that I can easily handle events in the FastAPI application.

#### Acceptance Criteria

1. WHEN a CloudEvent is received THEN the system SHALL parse it into a typed Python object
2. WHEN creating a CloudEvent THEN the system SHALL validate required attributes (id, source, type, specversion)
3. WHEN serializing a CloudEvent THEN the system SHALL support both structured and binary content modes
4. WHEN handling events THEN the system SHALL provide FastAPI dependency injection for CloudEvent parsing
5. WHEN CloudEvents are round-tripped (serialize then deserialize) THEN the system SHALL produce equivalent objects

