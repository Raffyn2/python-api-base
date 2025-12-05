# ADR-001: Dapr 1.14 Sidecar Integration

## Status

Accepted

## Context

The Python API Base project needs a standardized approach for building distributed microservices with features like service discovery, pub/sub messaging, state management, and resiliency patterns. Currently, these concerns are handled by individual libraries and custom implementations.

## Decision

We will integrate Dapr 1.14 as a sidecar runtime to provide:

1. **Service Invocation** - Service-to-service communication with automatic service discovery
2. **Pub/Sub Messaging** - Asynchronous messaging with CloudEvents
3. **State Management** - Pluggable state stores with transactions
4. **Secrets Management** - Secure secrets retrieval
5. **Bindings** - Integration with external systems
6. **Actors** - Virtual actors for stateful computation
7. **Workflows** - Long-running process orchestration
8. **Resiliency** - Built-in retry, timeout, and circuit breaker policies

## Rationale

### Why Dapr?

1. **Language Agnostic** - Works with any language via HTTP/gRPC APIs
2. **Pluggable Components** - Swap implementations without code changes
3. **Built-in Resiliency** - Declarative policies for fault tolerance
4. **Observability** - Automatic tracing and metrics
5. **Security** - mTLS between services by default
6. **CNCF Project** - Active community and enterprise adoption

### Alternatives Considered

1. **Direct SDK Integration** (Redis, Kafka, etc.)
   - Pros: Full control, no sidecar overhead
   - Cons: Tight coupling, manual resiliency, no abstraction

2. **Service Mesh (Istio/Linkerd)**
   - Pros: Network-level features, mTLS
   - Cons: Infrastructure complexity, no application-level features

3. **Custom Abstraction Layer**
   - Pros: Tailored to needs
   - Cons: Maintenance burden, reinventing the wheel

## Consequences

### Positive

- Simplified distributed systems development
- Consistent APIs across building blocks
- Easy component swapping (e.g., Redis to Cosmos DB)
- Built-in observability and security
- Reduced boilerplate code

### Negative

- Additional sidecar container per pod
- Learning curve for Dapr concepts
- Dependency on Dapr runtime
- Slight latency overhead for sidecar communication

### Neutral

- Requires Dapr installation in all environments
- Component configuration via YAML files
- Need to maintain Dapr version compatibility

## Implementation

1. Add Dapr Python SDK dependencies
2. Create infrastructure layer for Dapr integration
3. Configure components for state, pub/sub, secrets
4. Set up resiliency policies
5. Update deployment configurations
6. Add health checks and observability

## References

- [Dapr Documentation](https://docs.dapr.io/)
- [Dapr Python SDK](https://github.com/dapr/python-sdk)
- [Dapr Building Blocks](https://docs.dapr.io/concepts/building-blocks-concept/)
