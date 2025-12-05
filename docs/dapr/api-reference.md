# Dapr API Reference

## Overview

This document provides the API reference for the Dapr integration in the Python API Base project.

## Infrastructure Layer

### DaprClientWrapper

Central client for all Dapr operations.

```python
from infrastructure.dapr.client import DaprClientWrapper, get_dapr_client

# Get singleton instance
client = get_dapr_client()

# Initialize
await client.initialize()

# Use client
await client.publish_event("pubsub", "topic", data)

# Close
await client.close()
```

#### Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `initialize()` | Initialize client and wait for sidecar | None |
| `close()` | Close client and release resources | None |
| `invoke_method()` | Invoke remote service method | `app_id`, `method_name`, `data`, `http_verb`, `headers`, `timeout` |
| `publish_event()` | Publish event to topic | `pubsub_name`, `topic_name`, `data`, `data_content_type`, `metadata` |
| `get_state()` | Get state by key | `store_name`, `key`, `metadata` |
| `save_state()` | Save state | `store_name`, `key`, `value`, `etag`, `metadata` |
| `delete_state()` | Delete state | `store_name`, `key`, `etag` |
| `get_secret()` | Get secret | `store_name`, `key`, `metadata` |

### StateManager

Manages state store operations.

```python
from infrastructure.dapr.state import StateManager, StateItem

manager = StateManager(client, "statestore")

# Save state
await manager.save("key", b"value")

# Get state
item = await manager.get("key")

# Bulk operations
await manager.save_bulk([StateItem(key="k1", value=b"v1")])
items = await manager.get_bulk(["k1", "k2"])

# Transactions
await manager.transaction([
    {"operation": "upsert", "request": {"key": "k1", "value": "v1"}},
    {"operation": "delete", "request": {"key": "k2"}},
])

# Query (if supported)
results = await manager.query({"filter": {"EQ": {"field": "value"}}})
```

#### Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `get()` | Get state by key | `key` |
| `get_bulk()` | Get multiple states | `keys` |
| `save()` | Save state | `key`, `value`, `etag`, `options`, `ttl_seconds` |
| `save_bulk()` | Save multiple states | `items` |
| `delete()` | Delete state | `key`, `etag` |
| `transaction()` | Execute transaction | `operations` |
| `query()` | Query state store | `query` |

### PubSubManager

Manages pub/sub messaging.

```python
from infrastructure.dapr.pubsub import PubSubManager, CloudEvent, MessageStatus

manager = PubSubManager(client, "pubsub")

# Publish
await manager.publish("topic", {"data": "value"})

# Bulk publish
await manager.publish_bulk("topic", [{"msg": 1}, {"msg": 2}])

# Subscribe
async def handler(event: CloudEvent) -> MessageStatus:
    print(event.data)
    return MessageStatus.SUCCESS

manager.subscribe("topic", handler, dead_letter_topic="dlq")

# Get subscriptions for Dapr
subscriptions = manager.get_subscriptions()
```

#### Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `publish()` | Publish message | `topic`, `data`, `pubsub_name`, `options` |
| `publish_bulk()` | Publish batch | `topic`, `messages`, `pubsub_name`, `options` |
| `subscribe()` | Register handler | `topic`, `handler`, `pubsub_name`, `route`, `dead_letter_topic` |
| `get_subscriptions()` | Get all subscriptions | None |
| `handle_message()` | Handle incoming message | `pubsub_name`, `topic`, `event` |

### SecretsManager

Manages secrets retrieval.

```python
from infrastructure.dapr.secrets import SecretsManager

manager = SecretsManager(client, "secretstore")

# Get single secret
value = await manager.get_secret("api-key")

# Get from specific store
value = await manager.get_secret("api-key", store_name="vault")

# Get all secrets
secrets = await manager.get_bulk_secrets()

# Clear cache
manager.clear_cache()
```

#### Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `get_secret()` | Get single secret | `key`, `store_name`, `metadata`, `use_cache` |
| `get_bulk_secrets()` | Get all secrets | `store_name`, `metadata` |
| `clear_cache()` | Clear secrets cache | `store_name` |

### ServiceInvoker

Handles service-to-service invocation.

```python
from infrastructure.dapr.invoke import ServiceInvoker, HttpMethod

invoker = ServiceInvoker(client)

# HTTP invocation
response = await invoker.invoke(
    app_id="order-service",
    method_name="orders/123",
    http_verb=HttpMethod.GET,
)

# With retry
response = await invoker.invoke_with_retry(
    app_id="order-service",
    method_name="orders",
    data=b'{"item": "test"}',
    max_retries=3,
)

# gRPC invocation
result = await invoker.invoke_grpc(
    app_id="order-service",
    method_name="GetOrder",
    data=protobuf_data,
)
```

#### Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `invoke()` | Invoke HTTP method | `app_id`, `method_name`, `data`, `http_verb`, `headers`, `metadata`, `timeout` |
| `invoke_grpc()` | Invoke gRPC method | `app_id`, `method_name`, `data`, `metadata` |
| `invoke_with_retry()` | Invoke with retry | `app_id`, `method_name`, `data`, `http_verb`, `headers`, `max_retries`, `retry_delay` |

### BindingsManager

Manages input/output bindings.

```python
from infrastructure.dapr.bindings import BindingsManager, InputBindingEvent

manager = BindingsManager(client)

# Invoke output binding
response = await manager.invoke_binding(
    binding_name="kafka-output",
    operation="create",
    data={"message": "hello"},
)

# Register input binding handler
async def handler(event: InputBindingEvent) -> dict | None:
    print(f"Received: {event.data}")
    return {"processed": True}

manager.register_handler("cron", handler)
```

#### Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `invoke_binding()` | Invoke output binding | `binding_name`, `operation`, `data`, `metadata` |
| `register_handler()` | Register input handler | `binding_name`, `handler` |
| `handle_event()` | Handle input event | `binding_name`, `data`, `metadata` |
| `get_registered_bindings()` | List registered bindings | None |

### ActorRuntime

Manages virtual actors.

```python
from infrastructure.dapr.actors import Actor, ActorRuntime, ActorConfig

class OrderActor(Actor):
    async def on_activate(self) -> None:
        self.order = await self.get_state("order")
    
    async def on_deactivate(self) -> None:
        await self.set_state("order", self.order)
    
    async def process(self) -> None:
        await self.register_reminder("check", "1m", "1h")

# Configure runtime
config = ActorConfig(idle_timeout="1h")
runtime = ActorRuntime(config)
runtime.register_actor(OrderActor)

# Get actor config for Dapr
actor_config = runtime.get_actor_config()
```

#### Actor Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `on_activate()` | Called on activation | None |
| `on_deactivate()` | Called on deactivation | None |
| `get_state()` | Get actor state | `key` |
| `set_state()` | Set actor state | `key`, `value` |
| `remove_state()` | Remove actor state | `key` |
| `register_timer()` | Register timer | `name`, `callback`, `due_time`, `period`, `data` |
| `register_reminder()` | Register reminder | `name`, `due_time`, `period`, `data` |

### WorkflowEngine

Manages workflow execution.

```python
from infrastructure.dapr.workflow import Workflow, WorkflowActivity, WorkflowEngine

class ValidateOrder(WorkflowActivity):
    async def run(self, input: dict) -> dict:
        return {"valid": True, **input}

class OrderWorkflow(Workflow):
    async def run(self, ctx, input: dict) -> dict:
        result = await ctx.call_activity(ValidateOrder, input)
        return result

engine = WorkflowEngine(client)
engine.register_workflow(OrderWorkflow)
engine.register_activity(ValidateOrder)

# Start workflow
instance_id = await engine.start_workflow("OrderWorkflow", {"order_id": "123"})

# Get status
state = await engine.get_workflow_state(instance_id)

# Raise event
await engine.raise_event(instance_id, "payment_received", {"amount": 100})

# Terminate
await engine.terminate_workflow(instance_id, "cancelled by user")
```

#### Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `register_workflow()` | Register workflow | `workflow` |
| `register_activity()` | Register activity | `activity` |
| `start_workflow()` | Start workflow | `workflow_name`, `input`, `instance_id` |
| `get_workflow_state()` | Get workflow state | `instance_id` |
| `terminate_workflow()` | Terminate workflow | `instance_id`, `reason` |
| `raise_event()` | Raise event | `instance_id`, `event_name`, `data` |
| `pause_workflow()` | Pause workflow | `instance_id` |
| `resume_workflow()` | Resume workflow | `instance_id` |

### HealthChecker

Checks Dapr health.

```python
from infrastructure.dapr.health import HealthChecker, HealthStatus

checker = HealthChecker("http://localhost:3500")

# Check sidecar
status = await checker.check_sidecar_health()

# Check component
component = await checker.check_component_health("statestore", "state")

# Full health
health = await checker.get_full_health()

# Wait for sidecar
ready = await checker.wait_for_sidecar(timeout_seconds=60)

# Quick check
is_ready = await checker.is_ready()
```

#### Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `check_sidecar_health()` | Check sidecar health | None |
| `check_outbound_health()` | Check outbound health | None |
| `check_component_health()` | Check component health | `component_name`, `component_type` |
| `get_full_health()` | Get full health status | None |
| `wait_for_sidecar()` | Wait for sidecar ready | `timeout_seconds`, `poll_interval_seconds` |
| `is_ready()` | Quick ready check | None |

### MiddlewarePipeline

Manages middleware chain.

```python
from infrastructure.dapr.middleware import (
    MiddlewarePipeline,
    LoggingMiddleware,
    TracingMiddleware,
    ErrorHandlingMiddleware,
)

pipeline = MiddlewarePipeline()
pipeline.add(ErrorHandlingMiddleware())
pipeline.add(LoggingMiddleware())
pipeline.add(TracingMiddleware())

# Execute pipeline
response = await pipeline.execute(request, final_handler)

# Get middleware names
names = pipeline.get_middlewares()
```

## Error Types

```python
from infrastructure.dapr.errors import (
    DaprError,
    DaprConnectionError,
    DaprTimeoutError,
    StateNotFoundError,
    SecretNotFoundError,
    ActorInvocationError,
    WorkflowError,
    CircuitBreakerOpenError,
    ValidationError,
)
```

| Error | Description |
|-------|-------------|
| `DaprError` | Base exception |
| `DaprConnectionError` | Sidecar unavailable |
| `DaprTimeoutError` | Operation timed out |
| `StateNotFoundError` | State key not found |
| `SecretNotFoundError` | Secret not found |
| `ActorInvocationError` | Actor method failed |
| `WorkflowError` | Workflow operation failed |
| `CircuitBreakerOpenError` | Circuit breaker tripped |
| `ValidationError` | Input validation failed |

## Configuration

```python
from core.config.dapr import DaprSettings, get_dapr_settings

settings = get_dapr_settings()

# Available settings
settings.enabled           # Enable Dapr integration
settings.http_endpoint     # Dapr HTTP endpoint
settings.grpc_endpoint     # Dapr gRPC endpoint
settings.api_token         # API token for authentication
settings.app_id            # Application ID
settings.app_port          # Application port
settings.timeout_seconds   # Default timeout
settings.state_store_name  # Default state store
settings.pubsub_name       # Default pub/sub
settings.secret_store_name # Default secret store
```
