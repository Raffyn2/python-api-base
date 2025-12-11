"""Combined production middleware stack setup.

**Feature: python-api-base-2025-generics-audit**
**Validates: Requirements 13, 16, 18, 19, 22**
**Refactored: Split from production.py for one-class-per-file compliance**
"""

from typing import Any

import structlog

from infrastructure.audit import AuditStore
from infrastructure.feature_flags import FeatureFlagEvaluator
from interface.middleware.production.audit import AuditConfig, AuditMiddleware
from interface.middleware.production.feature_flags import FeatureFlagMiddleware
from interface.middleware.production.multitenancy import (
    MultitenancyConfig,
    MultitenancyMiddleware,
)
from interface.middleware.production.resilience import (
    ResilienceConfig,
    ResilienceMiddleware,
)

logger = structlog.get_logger(__name__)


def setup_production_middleware(
    app: Any,
    *,
    resilience_config: ResilienceConfig | None = None,
    multitenancy_config: MultitenancyConfig | None = None,
    feature_evaluator: FeatureFlagEvaluator[Any] | None = None,
    audit_store: AuditStore[Any] | None = None,
    audit_config: AuditConfig | None = None,
) -> None:
    """Setup complete production middleware stack.

    **Feature: python-api-base-2025-generics-audit**
    **Validates: Requirements 13, 16, 18, 19, 22**

    Usage:
        from interface.middleware.production import setup_production_middleware

        app = FastAPI()
        setup_production_middleware(
            app,
            resilience_config=ResilienceConfig(failure_threshold=10),
            multitenancy_config=MultitenancyConfig(required=True),
            audit_store=InMemoryAuditStore(),
        )
    """
    # Order matters: audit first (outermost), then resilience,
    # then tenant, then features
    if audit_store:
        app.add_middleware(
            AuditMiddleware,
            store=audit_store,
            config=audit_config,
        )
        logger.info("Audit middleware enabled")

    if resilience_config:
        app.add_middleware(ResilienceMiddleware, config=resilience_config)
        logger.info("Resilience middleware enabled")

    if multitenancy_config:
        app.add_middleware(MultitenancyMiddleware, config=multitenancy_config)
        logger.info("Multitenancy middleware enabled")

    if feature_evaluator:
        app.add_middleware(FeatureFlagMiddleware, evaluator=feature_evaluator)
        logger.info("Feature flag middleware enabled")
