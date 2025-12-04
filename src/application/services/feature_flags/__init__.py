"""Feature flags service for controlled feature rollouts.

Provides feature flag management with percentage-based rollouts,
user targeting, and custom evaluation rules using Strategy pattern.

**Feature: application-layer-improvements-2025**
**Validates: Requirements 10.1, 10.2, 10.3, Strategy pattern refactoring**
"""

from application.services.feature_flags.config import FlagConfig
from application.services.feature_flags.enums import FlagStatus, RolloutStrategy
from application.services.feature_flags.models import EvaluationContext
from application.services.feature_flags.service import FeatureFlagService
from application.services.feature_flags.strategies import (
    CustomRuleStrategy,
    DefaultValueStrategy,
    DisabledStrategy,
    EnabledStrategy,
    EvaluationStrategy,
    FlagEvaluationResult,
    GroupTargetingStrategy,
    PercentageRolloutStrategy,
    StrategyChain,
    UserTargetingStrategy,
    create_default_strategy_chain,
)

__all__ = [
    "CustomRuleStrategy",
    "DefaultValueStrategy",
    "DisabledStrategy",
    "EnabledStrategy",
    # Models
    "EvaluationContext",
    # Strategies
    "EvaluationStrategy",
    # Service
    "FeatureFlagService",
    "FlagConfig",
    "FlagEvaluationResult",
    # Enums
    "FlagStatus",
    "GroupTargetingStrategy",
    "PercentageRolloutStrategy",
    "RolloutStrategy",
    "StrategyChain",
    "UserTargetingStrategy",
    "create_default_strategy_chain",
]
