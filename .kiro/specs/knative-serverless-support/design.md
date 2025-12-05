# Design Document: Knative 1.15 Serverless Support

## Overview

Este documento descreve o design para adicionar suporte ao Knative 1.15 ao Python API Base. A implementação adiciona uma nova opção de deployment serverless nativa para Kubernetes, complementando as opções existentes (AWS Lambda, Vercel) e integrando-se com a infraestrutura já configurada (Istio, ArgoCD, Helm).

### Goals

1. Fornecer manifests Knative Serving para deploy serverless em Kubernetes
2. Configurar auto-scaling com scale-to-zero e concurrency-based scaling
3. Suportar traffic splitting para canary deployments
4. Integrar com Istio para mTLS e observability
5. Integrar com ArgoCD para GitOps deployment
6. Suportar Knative Eventing com Kafka e CloudEvents
7. Fornecer Python adapter para CloudEvents no FastAPI

### Non-Goals

1. Substituir deployments tradicionais (Helm, K8s manifests)
2. Implementar Knative Operator (usar instalação existente)
3. Suportar networking layers além de Istio e Kourier
4. Implementar custom autoscaler

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Knative Architecture                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         Knative Serving                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │   Service   │──│Configuration│──│  Revision   │──│    Route    │  │   │
│  │  │   (ksvc)    │  │             │  │  (v1, v2)   │  │  (traffic)  │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│                                      ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Networking Layer (Istio)                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │   │
│  │  │   Gateway   │  │VirtualService│  │DestinationRule│                │   │
│  │  │  (ingress)  │  │  (routing)  │  │   (mTLS)    │                   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│                                      ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        Knative Eventing                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │   │
│  │  │ KafkaSource │  │   Broker    │  │  Trigger    │                   │   │
│  │  │  (events)   │  │ (channel)   │  │  (filter)   │                   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Python API Base                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   FastAPI   │  │ CloudEvents │  │   Health    │  │   Metrics   │        │
│  │    App      │  │   Adapter   │  │   Probes    │  │  Exporter   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Knative Service Manifests

```
deployments/knative/
├── base/
│   ├── kustomization.yaml
│   ├── service.yaml           # Knative Service definition
│   ├── configmap.yaml         # Application configuration
│   └── serviceaccount.yaml    # RBAC
├── overlays/
│   ├── dev/
│   │   ├── kustomization.yaml
│   │   └── patches/
│   │       └── service-patch.yaml
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   └── patches/
│   │       └── service-patch.yaml
│   └── prod/
│       ├── kustomization.yaml
│       └── patches/
│           └── service-patch.yaml
├── eventing/
│   ├── kafka-source.yaml      # KafkaSource for events
│   ├── broker.yaml            # Event broker
│   └── trigger.yaml           # Event triggers
└── README.md
```

### 2. Knative Service Interface

```yaml
# base/service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: python-api-base
  namespace: my-api
  labels:
    app.kubernetes.io/name: python-api-base
    app.kubernetes.io/component: api
spec:
  template:
    metadata:
      annotations:
        # Autoscaling
        autoscaling.knative.dev/class: kpa.autoscaling.knative.dev
        autoscaling.knative.dev/metric: concurrency
        autoscaling.knative.dev/target: "100"
        autoscaling.knative.dev/min-scale: "0"
        autoscaling.knative.dev/max-scale: "10"
        autoscaling.knative.dev/scale-down-delay: "30s"
        # Istio sidecar
        sidecar.istio.io/inject: "true"
    spec:
      serviceAccountName: python-api-base
      containerConcurrency: 100
      timeoutSeconds: 300
      containers:
        - name: api
          image: python-api-base:latest
          ports:
            - containerPort: 8000
              protocol: TCP
          env:
            - name: ENVIRONMENT
              value: production
          envFrom:
            - configMapRef:
                name: python-api-base-config
            - secretRef:
                name: python-api-base-secrets
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 1000m
              memory: 1Gi
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 30
```

### 3. Traffic Splitting Interface

```yaml
# Traffic splitting for canary deployment
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: python-api-base
spec:
  traffic:
    - revisionName: python-api-base-v1
      percent: 90
      tag: stable
    - revisionName: python-api-base-v2
      percent: 10
      tag: canary
```

### 4. CloudEvents Python Adapter

```python
# src/infrastructure/eventing/cloudevents/
├── __init__.py
├── models.py          # CloudEvent Pydantic models
├── parser.py          # CloudEvent parser
├── serializer.py      # CloudEvent serializer
├── dependencies.py    # FastAPI dependencies
└── handler.py         # Event handler base class
```

#### CloudEvent Model Interface

```python
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime
from uuid import UUID

class CloudEvent(BaseModel):
    """CloudEvents v1.0 specification model."""
    
    # Required attributes
    id: str = Field(..., description="Event identifier")
    source: str = Field(..., description="Event source URI")
    type: str = Field(..., description="Event type")
    specversion: str = Field(default="1.0", description="CloudEvents spec version")
    
    # Optional attributes
    datacontenttype: Optional[str] = Field(default="application/json")
    dataschema: Optional[str] = None
    subject: Optional[str] = None
    time: Optional[datetime] = None
    
    # Event data
    data: Optional[Any] = None
    data_base64: Optional[str] = None
```

### 5. ArgoCD Integration

```yaml
# deployments/argocd/applications/knative-api.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-api-base-knative
  namespace: argocd
spec:
  project: python-api-base
  source:
    repoURL: https://github.com/org/python-api-base
    targetRevision: HEAD
    path: deployments/knative/overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: my-api
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## Data Models

### CloudEvent Model

```python
@dataclass
class CloudEventData:
    """Internal representation of CloudEvent."""
    id: str
    source: str
    type: str
    specversion: str = "1.0"
    datacontenttype: str = "application/json"
    dataschema: Optional[str] = None
    subject: Optional[str] = None
    time: Optional[datetime] = None
    data: Optional[dict[str, Any]] = None
    extensions: dict[str, Any] = field(default_factory=dict)
```

### Knative Service Configuration

```python
@dataclass
class KnativeServiceConfig:
    """Configuration for Knative Service generation."""
    name: str
    namespace: str
    image: str
    port: int = 8000
    
    # Autoscaling
    autoscaling_class: str = "kpa.autoscaling.knative.dev"
    autoscaling_metric: str = "concurrency"
    autoscaling_target: int = 100
    min_scale: int = 0
    max_scale: int = 10
    scale_down_delay: str = "30s"
    
    # Resources
    cpu_request: str = "100m"
    cpu_limit: str = "1000m"
    memory_request: str = "256Mi"
    memory_limit: str = "1Gi"
    
    # Container
    container_concurrency: int = 100
    timeout_seconds: int = 300
    
    # Istio
    istio_sidecar: bool = True
```

### Traffic Configuration

```python
@dataclass
class TrafficTarget:
    """Traffic target for revision."""
    revision_name: str
    percent: int
    tag: Optional[str] = None
    latest_revision: bool = False

@dataclass
class TrafficConfig:
    """Traffic splitting configuration."""
    targets: list[TrafficTarget]
    
    def validate(self) -> bool:
        """Validate traffic percentages sum to 100."""
        total = sum(t.percent for t in self.targets)
        return total == 100
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Based on the prework analysis, the following correctness properties have been identified:

### Property 1: Knative Service Manifest Round-Trip

*For any* valid KnativeServiceConfig, serializing it to YAML and deserializing back should produce an equivalent configuration object.

**Validates: Requirements 1.5, 2.5**

### Property 2: Traffic Percentage Validation

*For any* list of TrafficTarget objects, the validation should accept if and only if the percentages sum to exactly 100.

**Validates: Requirements 3.2, 3.5**

### Property 3: Traffic Configuration Generation

*For any* valid TrafficConfig, the generated Knative Service manifest should contain traffic entries matching the configuration.

**Validates: Requirements 3.1**

### Property 4: Kustomize Overlay Produces Valid Manifest

*For any* valid base configuration and environment overlay (dev/staging/prod), applying the overlay should produce a valid Knative Service manifest.

**Validates: Requirements 4.4, 4.5**

### Property 5: ArgoCD ApplicationSet Generation

*For any* valid ApplicationSet template and list of environments, the generated Applications should be valid ArgoCD Application manifests.

**Validates: Requirements 6.4, 6.5**

### Property 6: CloudEvent Validation

*For any* CloudEvent object, validation should accept if and only if all required attributes (id, source, type, specversion) are present and valid.

**Validates: Requirements 10.2**

### Property 7: CloudEvent Round-Trip

*For any* valid CloudEvent, serializing (in either structured or binary mode) and deserializing should produce an equivalent CloudEvent object.

**Validates: Requirements 8.5, 10.5**

### Property 8: CloudEvent Serialization Modes

*For any* valid CloudEvent, both structured and binary serialization modes should produce valid output that can be deserialized back to the original event.

**Validates: Requirements 10.3**

### Property 9: Autoscaling Annotation Generation

*For any* valid KnativeServiceConfig with autoscaling settings, the generated manifest should contain correct autoscaling annotations for the specified class (KPA or HPA).

**Validates: Requirements 2.3**

## Error Handling

### Manifest Validation Errors

```python
class KnativeManifestError(Exception):
    """Base error for Knative manifest issues."""
    pass

class InvalidTrafficConfigError(KnativeManifestError):
    """Traffic percentages don't sum to 100."""
    pass

class InvalidAutoscalingConfigError(KnativeManifestError):
    """Invalid autoscaling configuration."""
    pass
```

### CloudEvent Errors

```python
class CloudEventError(Exception):
    """Base error for CloudEvent issues."""
    pass

class CloudEventValidationError(CloudEventError):
    """CloudEvent missing required attributes."""
    pass

class CloudEventSerializationError(CloudEventError):
    """Error serializing/deserializing CloudEvent."""
    pass
```

## Testing Strategy

### Dual Testing Approach

This implementation uses both unit tests and property-based tests:

1. **Unit Tests**: Verify specific examples, edge cases, and integration points
2. **Property-Based Tests**: Verify universal properties across all valid inputs

### Property-Based Testing Framework

- **Library**: Hypothesis (Python)
- **Minimum iterations**: 100 per property
- **Configuration**: Use `@settings(max_examples=100)` decorator

### Test Structure

```
tests/
├── unit/
│   └── infrastructure/
│       └── knative/
│           ├── test_service_generator.py
│           ├── test_traffic_config.py
│           └── test_cloudevents.py
├── properties/
│   └── test_knative_properties.py
└── integration/
    └── test_knative_integration.py
```

### Property Test Annotations

Each property-based test must be annotated with:
- Feature name
- Property number
- Property description
- Requirements reference

Example:
```python
@given(st.builds(KnativeServiceConfig, ...))
@settings(max_examples=100)
def test_manifest_round_trip(config: KnativeServiceConfig):
    """
    **Feature: knative-serverless-support, Property 1: Knative Service Manifest Round-Trip**
    **Validates: Requirements 1.5, 2.5**
    """
    yaml_str = serialize_knative_service(config)
    parsed = deserialize_knative_service(yaml_str)
    assert config == parsed
```

### Unit Test Coverage

- Manifest generation with various configurations
- Traffic splitting edge cases (0%, 100%, multiple revisions)
- CloudEvent parsing (structured and binary modes)
- Error handling for invalid inputs
- FastAPI dependency injection

### Integration Test Coverage

- Kustomize overlay application
- ArgoCD Application generation
- End-to-end CloudEvent flow

