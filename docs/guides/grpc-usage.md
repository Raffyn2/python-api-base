# gRPC Usage Guide

Este guia explica como usar o suporte gRPC do Python API Base para comunicação entre microsserviços.

## Índice

- [Visão Geral](#visão-geral)
- [Configuração](#configuração)
- [Criando um Serviço](#criando-um-serviço)
- [Implementando um Servicer](#implementando-um-servicer)
- [Usando o Cliente](#usando-o-cliente)
- [Interceptors](#interceptors)
- [Health Checks](#health-checks)
- [Troubleshooting](#troubleshooting)

## Visão Geral

O suporte gRPC permite comunicação eficiente entre microsserviços usando:

- **Protocol Buffers** para serialização binária
- **HTTP/2** para multiplexação e streaming
- **Interceptors** para cross-cutting concerns
- **Health Checks** para integração com Kubernetes

## Configuração

### Variáveis de Ambiente

```bash
# Server
GRPC__SERVER__ENABLED=true
GRPC__SERVER__HOST=0.0.0.0
GRPC__SERVER__PORT=50051
GRPC__SERVER__REFLECTION_ENABLED=true
GRPC__SERVER__HEALTH_CHECK_ENABLED=true

# Client
GRPC__CLIENT__DEFAULT_TIMEOUT=30.0
GRPC__CLIENT__MAX_RETRIES=3
GRPC__CLIENT__CIRCUIT_BREAKER_THRESHOLD=5
```

### Dependências

As dependências gRPC já estão incluídas no `pyproject.toml`:

```toml
"grpcio>=1.68.0",
"grpcio-tools>=1.68.0",
"grpcio-health-checking>=1.68.0",
"grpcio-reflection>=1.68.0",
```

## Criando um Serviço

### 1. Definir o Proto

Crie um arquivo `.proto` em `protos/`:

```protobuf
// protos/myservice/service.proto
syntax = "proto3";
package myservice;

service MyService {
  rpc GetResource(GetResourceRequest) returns (Resource);
  rpc ListResources(ListResourcesRequest) returns (stream Resource);
}

message GetResourceRequest {
  string id = 1;
}

message Resource {
  string id = 1;
  string name = 2;
}

message ListResourcesRequest {
  int32 page_size = 1;
}
```

### 2. Gerar Código Python

```bash
make proto-gen
```

Isso gera os arquivos em `src/infrastructure/grpc/generated/`.

## Implementando um Servicer

### 1. Criar o Servicer

```python
# src/interface/grpc/servicers/myservice.py
from src.interface.grpc.servicers.base import BaseServicer

class MyServiceServicer(BaseServicer):
    async def GetResource(self, request, context):
        resource_id = request.id
        
        # Use case from DI container
        use_case = self.get_use_case(GetResourceUseCase)
        result = await use_case.execute(resource_id)
        
        if result is None:
            await context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Resource {resource_id} not found"
            )
            return
        
        return self._to_proto(result)
    
    async def ListResources(self, request, context):
        page_size = request.page_size or 10
        
        use_case = self.get_use_case(ListResourcesUseCase)
        async for resource in use_case.execute(page_size):
            yield self._to_proto(resource)
```

### 2. Registrar no Server

```python
# src/main.py
from src.infrastructure.grpc import GRPCServer
from src.interface.grpc.servicers.myservice import MyServiceServicer

async def start_grpc_server():
    server = GRPCServer(
        port=50051,
        interceptors=[
            AuthInterceptor(jwt_validator),
            LoggingInterceptor(),
            TracingInterceptor(),
            MetricsInterceptor(),
        ],
    )
    
    server.add_servicer(
        MyServiceServicer(),
        add_MyServiceServicer_to_server,
    )
    
    await server.start()
```

## Usando o Cliente

### 1. Criar o Cliente

```python
from src.infrastructure.grpc.client import GRPCClientFactory

async def get_client():
    factory = GRPCClientFactory(
        default_timeout=30.0,
    )
    
    channel = await factory.create_channel(
        "myservice:50051",
        secure=False,  # Use True em produção com TLS
    )
    
    stub = factory.create_stub(MyServiceStub, channel)
    return stub
```

### 2. Fazer Chamadas

```python
# Unary
stub = await get_client()
response = await stub.GetResource(GetResourceRequest(id="123"))

# Server Streaming
async for resource in stub.ListResources(ListResourcesRequest(page_size=10)):
    print(resource.name)
```

## Interceptors

### Interceptors Disponíveis

| Interceptor | Descrição |
|-------------|-----------|
| `AuthInterceptor` | Valida JWT tokens |
| `LoggingInterceptor` | Log de requests com correlation ID |
| `TracingInterceptor` | OpenTelemetry spans |
| `MetricsInterceptor` | Métricas Prometheus |
| `ErrorInterceptor` | Tratamento de erros |

### Ordem de Execução

```python
interceptors = [
    ErrorInterceptor(),      # 1. Captura erros
    MetricsInterceptor(),    # 2. Métricas
    TracingInterceptor(),    # 3. Tracing
    LoggingInterceptor(),    # 4. Logging
    AuthInterceptor(...),    # 5. Autenticação
]
```

## Health Checks

### Kubernetes Probes

```yaml
livenessProbe:
  grpc:
    port: 50051
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  grpc:
    port: 50051
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Verificar com grpcurl

```bash
# Health check
grpcurl -plaintext localhost:50051 grpc.health.v1.Health/Check

# List services (reflection)
grpcurl -plaintext localhost:50051 list
```

## Troubleshooting

### Erro: "Connection refused"

1. Verifique se o servidor está rodando
2. Verifique a porta correta
3. Verifique firewall/network policies

### Erro: "UNAUTHENTICATED"

1. Verifique se o token JWT está no header `authorization`
2. Formato: `Bearer <token>`
3. Verifique se o token não expirou

### Erro: "DEADLINE_EXCEEDED"

1. Aumente o timeout do cliente
2. Verifique latência de rede
3. Verifique se o servidor está sobrecarregado

### Debug com Reflection

```bash
# Listar serviços
grpcurl -plaintext localhost:50051 list

# Descrever serviço
grpcurl -plaintext localhost:50051 describe myservice.MyService

# Chamar método
grpcurl -plaintext -d '{"id": "123"}' \
  localhost:50051 myservice.MyService/GetResource
```

### Logs

Os logs gRPC usam structlog com formato JSON:

```json
{
  "event": "grpc_request_completed",
  "method": "/myservice.MyService/GetResource",
  "correlation_id": "abc-123",
  "duration_ms": 15.5,
  "status": "OK"
}
```
