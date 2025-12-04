"""Application startup and shutdown lifecycle management.

**Feature: code-review-2025**
**Refactored from: main.py (604 lines)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from core.config import get_settings
from core.shared.logging import get_logger
from infrastructure.db.repositories.examples import (
    ItemExampleRepository,
    PedidoExampleRepository,
)
from infrastructure.db.session import (
    close_database,
    get_database_session,
    init_database,
)
from infrastructure.di import lifecycle
from infrastructure.di.app_container import create_container
from infrastructure.di.cqrs_bootstrap import bootstrap_cqrs
from infrastructure.di.examples_bootstrap import bootstrap_examples

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = get_logger(__name__)


async def initialize_database() -> None:
    """Initialize database connection pool."""
    settings = get_settings()
    logger.info("Initializing database...")
    init_database(
        database_url=settings.database.url,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        echo=settings.database.echo,
    )
    logger.info("Database initialized")


async def initialize_cqrs() -> tuple[Any, Any]:
    """Bootstrap CQRS command and query buses.

    Returns:
        Tuple of (command_bus, query_bus)
    """
    settings = get_settings()
    logger.info("Bootstrapping CQRS handlers...")
    container = create_container(settings)
    command_bus = container.command_bus()
    query_bus = container.query_bus()
    await bootstrap_cqrs(command_bus=command_bus, query_bus=query_bus)
    logger.info("CQRS handlers bootstrapped")
    return command_bus, query_bus


async def initialize_examples(command_bus: Any, query_bus: Any) -> None:
    """Bootstrap example handlers."""
    logger.info("Bootstrapping example handlers...")
    db = get_database_session()
    async with db.session() as session:
        item_repo = ItemExampleRepository(session)
        pedido_repo = PedidoExampleRepository(session)
        await bootstrap_examples(
            command_bus=command_bus,
            query_bus=query_bus,
            item_repository=item_repo,
            pedido_repository=pedido_repo,
        )
    logger.info("Example handlers bootstrapped")


async def initialize_jwks() -> None:
    """Initialize JWKS service for JWT RS256 verification."""
    settings = get_settings()
    from infrastructure.auth.jwt.jwks import initialize_jwks_service

    try:
        jwt_settings = getattr(settings, "jwt", None)
        if (
            jwt_settings
            and hasattr(jwt_settings, "private_key")
            and jwt_settings.private_key
        ):
            initialize_jwks_service(
                private_key_pem=jwt_settings.private_key,
                algorithm=getattr(jwt_settings, "algorithm", "RS256"),
            )
            logger.info("JWKS service initialized with configured key")
        else:
            _initialize_ephemeral_jwks()
    except Exception as e:
        logger.error(f"JWKS initialization failed: {e}")


def _initialize_ephemeral_jwks() -> None:
    """Initialize JWKS with ephemeral key for development."""
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    from infrastructure.auth.jwt.jwks import initialize_jwks_service

    private_key = rsa.generate_private_key(65537, 2048, default_backend())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    initialize_jwks_service(private_key_pem=private_pem, algorithm="RS256")
    logger.warning(
        "JWKS using ephemeral key - configure JWT_PRIVATE_KEY for production"
    )


async def initialize_redis(app: FastAPI) -> None:
    """Initialize Redis client and idempotency handler."""
    settings = get_settings()
    obs = settings.observability

    if not obs.redis_enabled:
        app.state.redis = None
        app.state.idempotency_handler = None
        return

    from infrastructure.idempotency import IdempotencyConfig, IdempotencyHandler
    from infrastructure.redis import RedisClient, RedisConfig

    redis_config = RedisConfig(
        url=obs.redis_url,
        pool_max_size=obs.redis_pool_size,
        key_prefix=obs.redis_key_prefix,
    )
    app.state.redis = RedisClient(redis_config)
    await app.state.redis.connect()

    app.state.idempotency_handler = IdempotencyHandler(
        redis_url=obs.redis_url,
        config=IdempotencyConfig(
            ttl_hours=24,
            key_prefix="api:idempotency",
        ),
    )
    await app.state.idempotency_handler.connect()
    logger.info("Idempotency handler initialized")


async def initialize_minio(app: FastAPI) -> None:
    """Initialize MinIO client."""
    settings = get_settings()
    obs = settings.observability

    if not obs.minio_enabled:
        app.state.minio = None
        return

    from infrastructure.minio import MinIOClient, MinIOConfig

    minio_config = MinIOConfig(
        endpoint=obs.minio_endpoint,
        access_key=obs.minio_access_key,
        secret_key=obs.minio_secret_key.get_secret_value(),
        bucket=obs.minio_bucket,
        secure=obs.minio_secure,
    )
    app.state.minio = MinIOClient(minio_config)
    await app.state.minio.connect()


async def initialize_kafka(app: FastAPI) -> None:
    """Initialize Kafka producer."""
    settings = get_settings()
    obs = settings.observability

    if not obs.kafka_enabled:
        app.state.kafka_producer = None
        logger.info("Kafka disabled, skipping initialization")
        return

    from infrastructure.kafka import KafkaConfig, KafkaProducer

    kafka_config = KafkaConfig(
        bootstrap_servers=obs.kafka_bootstrap_servers,
        client_id=obs.kafka_client_id,
        group_id=obs.kafka_group_id,
        security_protocol=obs.kafka_security_protocol,
        sasl_mechanism=obs.kafka_sasl_mechanism,
        sasl_username=obs.kafka_sasl_username,
        sasl_password=obs.kafka_sasl_password.get_secret_value()
        if obs.kafka_sasl_password
        else None,
    )
    app.state.kafka_producer = KafkaProducer(kafka_config, topic="default-events")
    try:
        await app.state.kafka_producer.start()
        logger.info("Kafka producer started")
    except Exception as e:
        logger.error(f"Kafka connection failed: {e}")
        app.state.kafka_producer = None


async def initialize_scylladb(app: FastAPI) -> None:
    """Initialize ScyllaDB client."""
    settings = get_settings()
    obs = settings.observability

    if not obs.scylladb_enabled:
        app.state.scylladb = None
        logger.info("ScyllaDB disabled, skipping initialization")
        return

    from infrastructure.scylladb import ScyllaDBClient, ScyllaDBConfig

    scylladb_config = ScyllaDBConfig(
        hosts=obs.scylladb_hosts,
        port=obs.scylladb_port,
        keyspace=obs.scylladb_keyspace,
        username=obs.scylladb_username,
        password=obs.scylladb_password.get_secret_value()
        if obs.scylladb_password
        else None,
        protocol_version=obs.scylladb_protocol_version,
        connect_timeout=obs.scylladb_connect_timeout,
        request_timeout=obs.scylladb_request_timeout,
    )
    app.state.scylladb = ScyllaDBClient(scylladb_config)
    try:
        await app.state.scylladb.connect()
        logger.info("ScyllaDB client connected")
    except Exception as e:
        logger.error(f"ScyllaDB connection failed: {e}")
        app.state.scylladb = None


async def initialize_rabbitmq(app: FastAPI) -> None:
    """Initialize RabbitMQ configuration."""
    settings = get_settings()
    obs = settings.observability

    if not obs.rabbitmq_enabled:
        app.state.rabbitmq = None
        logger.info("RabbitMQ disabled, skipping initialization")
        return

    from infrastructure.tasks import RabbitMQConfig

    rabbitmq_config = RabbitMQConfig(
        host=obs.rabbitmq_host,
        port=obs.rabbitmq_port,
        username=obs.rabbitmq_username,
        password=obs.rabbitmq_password.get_secret_value()
        if obs.rabbitmq_password
        else None,
        virtual_host=obs.rabbitmq_virtual_host,
    )
    app.state.rabbitmq = rabbitmq_config
    logger.info("RabbitMQ config stored (lazy connection)")


async def cleanup_resources(app: FastAPI) -> None:
    """Cleanup all resources on shutdown."""
    if app.state.redis:
        await app.state.redis.close()

    if app.state.kafka_producer:
        await app.state.kafka_producer.stop()
        logger.info("Kafka producer stopped")

    if hasattr(app.state, "scylladb") and app.state.scylladb:
        await app.state.scylladb.close()
        logger.info("ScyllaDB client closed")

    logger.info("Closing database...")
    await close_database()
    logger.info("Database closed")

    await lifecycle.run_shutdown_async()
    lifecycle.run_shutdown()
