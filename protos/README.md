# Protocol Buffers

Este diretório contém as definições Protocol Buffers (proto3) para a API gRPC do Python API Base.

## Estrutura

```
protos/
├── buf.yaml           # Configuração do Buf (lint, breaking, deps)
├── buf.gen.yaml       # Configuração de geração de código
├── common/
│   └── v1/
│       ├── errors.proto      # Tipos de erro padronizados
│       ├── health.proto      # Health check (gRPC standard)
│       └── pagination.proto  # Paginação reutilizável
└── examples/
    └── v1/
        └── items.proto       # Serviço de exemplo (CRUD)
```

## Convenções

### Versionamento de Pacotes

Todos os pacotes seguem o padrão `{domain}.v{version}`:
- `common.v1` - Tipos comuns compartilhados
- `examples.v1` - Serviços de exemplo

### Nomenclatura

| Elemento | Convenção | Exemplo |
|----------|-----------|---------|
| Package | `lower_snake_case.v1` | `common.v1` |
| Service | `PascalCase` + `Service` | `ItemService` |
| RPC | `PascalCase` | `GetItem`, `ListItems` |
| Message | `PascalCase` | `GetItemRequest` |
| Field | `lower_snake_case` | `page_size`, `create_time` |
| Enum | `PascalCase` | `ErrorCode` |
| Enum Value | `UPPER_SNAKE_CASE` + prefix | `ERROR_CODE_NOT_FOUND` |

### Request/Response

Cada RPC tem mensagens únicas de request e response:
- `GetItem` → `GetItemRequest` / `GetItemResponse`
- `CreateItem` → `CreateItemRequest` / `CreateItemResponse`

### Validação

Usamos [protovalidate](https://github.com/bufbuild/protovalidate) para validação:

```protobuf
message CreateItemRequest {
  string display_name = 1 [(buf.validate.field) = {
    required: true,
    string: {min_len: 1, max_len: 255}
  }];
}
```

### Timestamps

Sempre use `google.protobuf.Timestamp` para campos de data/hora:

```protobuf
import "google/protobuf/timestamp.proto";

message Item {
  google.protobuf.Timestamp create_time = 10;
}
```

### Paginação

Use os tipos de `common.v1.pagination`:

```protobuf
import "common/v1/pagination.proto";

message ListItemsRequest {
  common.v1.PageRequest page = 1;
}

message ListItemsResponse {
  repeated Item items = 1;
  common.v1.PageResponse page = 2;
}
```

### Field Masks

Para updates parciais, use `google.protobuf.FieldMask`:

```protobuf
import "google/protobuf/field_mask.proto";

message UpdateItemRequest {
  Item item = 1;
  google.protobuf.FieldMask update_mask = 2;
}
```

## Comandos

### Lint

```bash
cd protos
buf lint
```

### Geração de Código

```bash
cd protos
buf generate
```

Os arquivos são gerados em `src/infrastructure/grpc/generated/`.

### Breaking Changes

```bash
cd protos
buf breaking --against '.git#branch=main'
```

### Atualizar Dependências

```bash
cd protos
buf dep update
```

## Dependências

- `buf.build/googleapis/googleapis` - Well-known types (Timestamp, Duration, FieldMask)
- `buf.build/bufbuild/protovalidate` - Validação de campos

## Referências

- [Google AIP](https://google.aip.dev/) - API Improvement Proposals
- [Buf Style Guide](https://buf.build/docs/best-practices/style-guide)
- [gRPC Best Practices](https://grpc.io/docs/guides/performance/)
