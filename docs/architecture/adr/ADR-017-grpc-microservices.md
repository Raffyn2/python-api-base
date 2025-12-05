# ADR-017: gRPC Support for Microservices Communication

## Status

Accepted

## Date

2024-12-04

## Context

O Python API Base precisa suportar comunicação eficiente entre microsserviços. A API REST existente é adequada para clientes externos, mas para comunicação interna service-to-service, precisamos de:

- Alta performance e baixa latência
- Type safety através de contratos fortemente tipados
- Suporte a streaming bidirecional
- Integração com service mesh (Istio)
- Observabilidade completa

## Decision

Adotamos gRPC como protocolo de comunicação para microsserviços internos, complementando a API REST existente.

### Componentes Implementados

1. **gRPC Server** (`src/infrastructure/grpc/server.py`)
   - Servidor async com suporte a interceptors
   - Health checks e reflection
   - Graceful shutdown

2. **Interceptors** (`src/infrastructure/grpc/interceptors/`)
   - Authentication (JWT)
   - Logging (structlog)
   - Tracing (OpenTelemetry)
   - Metrics (Prometheus)
   - Error handling

3. **Client Factory** (`src/infrastructure/grpc/client/`)
   - Connection pooling
   - Retry com exponential backoff
   - Circuit breaker

4. **Health Service** (`src/infrastructure/grpc/health/`)
   - Protocolo padrão gRPC health checking
   - Integração com Kubernetes probes

## Alternatives Considered

### 1. REST para Comunicação Interna

**Prós:**
- Já implementado
- Familiar para desenvolvedores
- Ferramentas maduras

**Contras:**
- Overhead de serialização JSON
- Sem type safety em runtime
- Sem streaming nativo

### 2. GraphQL Federation

**Prós:**
- Schema unificado
- Flexibilidade de queries

**Contras:**
- Complexidade adicional
- Overhead para comunicação interna
- Não otimizado para service-to-service

### 3. Message Queue (Kafka/RabbitMQ)

**Prós:**
- Desacoplamento
- Resiliência

**Contras:**
- Não adequado para request/response
- Latência adicional
- Já temos Kafka para eventos

## Consequences

### Positive

- **Performance**: HTTP/2 + Protobuf = ~10x mais rápido que REST/JSON
- **Type Safety**: Contratos definidos em `.proto` files
- **Streaming**: Suporte nativo a streaming bidirecional
- **Observabilidade**: Integração com OpenTelemetry e Prometheus
- **Kubernetes**: Health checks nativos para probes
- **Istio**: Suporte completo a mTLS e traffic management

### Negative

- **Complexidade**: Mais uma tecnologia para manter
- **Curva de Aprendizado**: Desenvolvedores precisam aprender Protobuf
- **Debugging**: Mais difícil que REST (binário)
- **Browser**: Não suporta browsers diretamente (precisa gRPC-Web)

### Neutral

- **Coexistência**: REST e gRPC coexistem no mesmo serviço
- **Porta Adicional**: gRPC usa porta 50051 separada

## Implementation Notes

### Estrutura de Diretórios

```
src/infrastructure/grpc/
├── server.py           # gRPC server
├── interceptors/       # Server interceptors
├── client/             # Client factory
├── health/             # Health service
└── utils/              # Mappers, status codes

protos/
├── common/             # Shared protos
└── examples/           # Example service
```

### Configuração

```python
# .env
GRPC__SERVER__ENABLED=true
GRPC__SERVER__PORT=50051
GRPC__SERVER__REFLECTION_ENABLED=true
GRPC__CLIENT__DEFAULT_TIMEOUT=30.0
GRPC__CLIENT__MAX_RETRIES=3
```

### Uso

```python
# Server
from src.infrastructure.grpc import GRPCServer

server = GRPCServer(port=50051)
server.add_servicer(MyServicer(), add_MyServicer_to_server)
await server.start()

# Client
from src.infrastructure.grpc.client import GRPCClientFactory

factory = GRPCClientFactory()
channel = await factory.create_channel("service:50051")
stub = factory.create_stub(MyServiceStub, channel)
```

## References

- [gRPC Documentation](https://grpc.io/docs/)
- [Protocol Buffers](https://protobuf.dev/)
- [gRPC Health Checking Protocol](https://github.com/grpc/grpc/blob/master/doc/health-checking.md)
- [Istio gRPC Support](https://istio.io/latest/docs/ops/configuration/traffic-management/protocol-selection/)
